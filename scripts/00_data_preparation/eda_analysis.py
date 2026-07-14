#!/usr/bin/env python3
"""
Exhaustive Exploratory Data Analysis & Strengthening Model Fitting
for FCC HEA Grain Size / Mechanical Property Dataset

Al-Co-Cr-Cu-Fe-Mn-Ni-V system
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
from sklearn.linear_model import LinearRegression, Lasso, Ridge, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, LeaveOneOut, RepeatedKFold
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# PATHS
# ============================================================
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/ (for _config)
from _config import REPO_ROOT, DATA_DIR, RAW_DATA_DIR, RESULTS_DIR, PLOTS_DIR, PAPER_DIR, PAPER_FIG_DIR
BASE = str(REPO_ROOT)
PLOT_DIR = f'{PLOTS_DIR}'
XLSX = f'{RAW_DATA_DIR}/Grain_Size_Summary_v3.xlsx'

# ============================================================
# ELEMENT PARAMETERS
# ============================================================
ELEMENTS = ['Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'Ni', 'V']

# Metallic (Goldschmidt) radii in pm
RADII = {'Al': 143, 'Co': 125, 'Cr': 128, 'Cu': 128, 'Fe': 126, 'Mn': 127, 'Ni': 124, 'V': 134}

# Valence electron concentration
VEC_VALS = {'Al': 3, 'Co': 9, 'Cr': 6, 'Cu': 11, 'Fe': 8, 'Mn': 7, 'Ni': 10, 'V': 5}

# Pauling electronegativity
EN = {'Al': 1.61, 'Co': 1.88, 'Cr': 1.66, 'Cu': 1.90, 'Fe': 1.83, 'Mn': 1.55, 'Ni': 1.91, 'V': 1.63}

# Melting points (K)
TM = {'Al': 933, 'Co': 1768, 'Cr': 2180, 'Cu': 1358, 'Fe': 1811, 'Mn': 1519, 'Ni': 1728, 'V': 2183}

# Shear modulus (GPa)
SHEAR_MOD = {'Al': 26, 'Co': 75, 'Cr': 115, 'Cu': 48, 'Fe': 82, 'Mn': 79, 'Ni': 76, 'V': 47}  # Co: 75 GPa (polycrystalline FCC)

# FCC lattice parameters (Angstrom, extrapolated for non-FCC elements)
A_FCC = {'Al': 4.050, 'Co': 3.545, 'Cr': 3.520, 'Cu': 3.615, 'Fe': 3.590, 'Mn': 3.540, 'Ni': 3.524, 'V': 3.720}  # Fe: 3.590 Å (gamma-Fe FCC)

# Miedema binary mixing enthalpies (kJ/mol) — from Takeuchi & Inoue (2005)
# Upper triangle of symmetric matrix: HMIX[i][j] for i<j
HMIX = {
    ('Al','Co'): -19, ('Al','Cr'): -10, ('Al','Cu'): -1, ('Al','Fe'): -11,
    ('Al','Mn'): -19, ('Al','Ni'): -22, ('Al','V'): -16,
    ('Co','Cr'): -4,  ('Co','Cu'): 6,   ('Co','Fe'): -1, ('Co','Mn'): -5,
    ('Co','Ni'): 0,   ('Co','V'): -14,
    ('Cr','Cu'): 12,  ('Cr','Fe'): -1,  ('Cr','Mn'): 2,  ('Cr','Ni'): -7,
    ('Cr','V'): -2,
    ('Cu','Fe'): 13,  ('Cu','Mn'): 4,   ('Cu','Ni'): 4,  ('Cu','V'): 5,
    ('Fe','Mn'): 0,   ('Fe','Ni'): -2,  ('Fe','V'): -7,
    ('Mn','Ni'): -8,  ('Mn','V'): -1,
    ('Ni','V'): -18,
}

R_GAS = 8.314  # J/(mol·K)

# ============================================================
# LOAD DATA
# ============================================================
print("=" * 70)
print("LOADING DATA")
print("=" * 70)
df = pd.read_excel(XLSX, sheet_name='GS_MasterTable_Iterations ')

# Rename columns for convenience
df.columns = ['Iteration', 'Alloy', 'Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'Ni', 'V',
              'HV', 'SD_HV', 'YS', 'SD_YS', 'ColdWork', 'RecrystT', 'HoldTime',
              'GrainSize', 'SD_GS']

# Convert compositions from at% to fractions
for el in ELEMENTS:
    df[f'{el}_frac'] = df[el] / 100.0

print(f"Loaded {len(df)} alloys across {df['Iteration'].nunique()} batches")
print(f"Batches: {df['Iteration'].value_counts().to_dict()}")
print(f"\nMissing YS: {df['YS'].isna().sum()}, Missing SD_YS: {df['SD_YS'].isna().sum()}")

# ============================================================
# COMPUTE HEA DESCRIPTORS
# ============================================================
print("\n" + "=" * 70)
print("COMPUTING HEA DESCRIPTORS")
print("=" * 70)


def compute_descriptors(row):
    """Compute all HEA descriptors for a single alloy."""
    fracs = {el: row[f'{el}_frac'] for el in ELEMENTS}
    active = {el: c for el, c in fracs.items() if c > 0}

    # Number of components
    n_comp = len(active)

    # Average radius
    r_bar = sum(c * RADII[el] for el, c in fracs.items())

    # Atomic size difference delta
    delta = np.sqrt(sum(c * (1 - RADII[el] / r_bar) ** 2 for el, c in fracs.items()))

    # Mixing entropy
    dS_mix = -R_GAS * sum(c * np.log(c) for c in active.values())

    # VEC
    vec = sum(c * VEC_VALS[el] for el, c in fracs.items())

    # Electronegativity difference
    en_bar = sum(c * EN[el] for el, c in fracs.items())
    delta_chi = np.sqrt(sum(c * (EN[el] - en_bar) ** 2 for el, c in fracs.items()))

    # Average melting point
    tm_bar = sum(c * TM[el] for el, c in fracs.items())

    # Average shear modulus (Voigt)
    mu_bar = sum(c * SHEAR_MOD[el] for el, c in fracs.items())

    # Modulus mismatch
    delta_mu = np.sqrt(sum(c * (1 - SHEAR_MOD[el] / mu_bar) ** 2 for el, c in fracs.items()))

    # Mixing enthalpy (Miedema)
    dH_mix = 0.0
    for i, el_i in enumerate(ELEMENTS):
        for j, el_j in enumerate(ELEMENTS):
            if i < j:
                key = (el_i, el_j) if (el_i, el_j) in HMIX else (el_j, el_i)
                if key in HMIX:
                    dH_mix += 4 * HMIX[key] * fracs[el_i] * fracs[el_j]

    # Omega parameter
    omega = tm_bar * dS_mix / (abs(dH_mix) * 1000) if abs(dH_mix) > 0.01 else np.inf

    # VLC misfit volume parameter (Phi_VLC)
    # Approximate V_n ~ (4/3)pi r_n^3
    V = {el: (4 / 3) * np.pi * (RADII[el] * 1e-12) ** 3 for el in ELEMENTS}
    V_bar = sum(c * V[el] for el, c in fracs.items())
    a_bar = sum(c * A_FCC[el] for el, c in fracs.items())  # Angstrom
    b_burg = a_bar / np.sqrt(2) * 1e-10  # meters
    sigma_dV2 = sum(c * (V[el] - V_bar) ** 2 for el, c in fracs.items())
    phi_vlc = sigma_dV2 / b_burg ** 6

    # Labusch combined misfit parameter
    alpha_L = 16  # for edge dislocations in FCC
    delta_r_i = {el: (RADII[el] - r_bar) / r_bar for el in ELEMENTS}
    delta_mu_i = {el: (SHEAR_MOD[el] - mu_bar) / mu_bar for el in ELEMENTS}
    eps_L = np.sqrt(
        sum(c * delta_mu_i[el] ** 2 for el, c in fracs.items())
        + alpha_L ** 2 * sum(c * delta_r_i[el] ** 2 for el, c in fracs.items())
    )

    return pd.Series({
        'n_comp': n_comp,
        'delta': delta,
        'dS_mix': dS_mix,
        'VEC': vec,
        'delta_chi': delta_chi,
        'Tm_bar': tm_bar,
        'mu_bar': mu_bar,
        'delta_mu': delta_mu,
        'dH_mix': dH_mix,
        'Omega': omega,
        'Phi_VLC': phi_vlc,
        'eps_Labusch': eps_L,
        'a_bar': a_bar,
    })


desc = df.apply(compute_descriptors, axis=1)
df = pd.concat([df, desc], axis=1)

# Derived features
df['d_inv_sqrt'] = df['GrainSize'] ** (-0.5)
df['log_d'] = np.log10(df['GrainSize'])

print("\nDescriptor statistics:")
desc_cols = ['n_comp', 'delta', 'dS_mix', 'VEC', 'delta_chi', 'Tm_bar', 'mu_bar',
             'delta_mu', 'dH_mix', 'Omega', 'Phi_VLC', 'eps_Labusch']
print(df[desc_cols].describe().round(4).to_string())

# Save augmented data
df.to_csv(f'{DATA_DIR}/data_with_descriptors.csv', index=False)
print(f"\nSaved augmented data to data_with_descriptors.csv")

# ============================================================
# 1. BASIC STATISTICS
# ============================================================
print("\n" + "=" * 70)
print("1. BASIC STATISTICS")
print("=" * 70)

print("\nComposition ranges (at%):")
for el in ELEMENTS:
    print(f"  {el:2s}: {df[el].min():5.1f} - {df[el].max():5.1f}  (mean={df[el].mean():5.1f})")

print(f"\nHardness: {df['HV'].min():.1f} - {df['HV'].max():.1f} HV (mean={df['HV'].mean():.1f})")
print(f"YS:       {df['YS'].min():.1f} - {df['YS'].max():.1f} MPa (mean={df['YS'].mean():.1f})")
print(f"Grain Size: {df['GrainSize'].min():.1f} - {df['GrainSize'].max():.1f} µm (mean={df['GrainSize'].mean():.1f})")

print(f"\nProcessing:")
print(f"  Cold Work: {sorted(df['ColdWork'].unique())}")
print(f"  Recryst T: {df['RecrystT'].min()} - {df['RecrystT'].max()} C")
print(f"  Hold Time: {sorted(df['HoldTime'].unique())}")

# ============================================================
# 2. CORRELATION ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("2. CORRELATION ANALYSIS")
print("=" * 70)

corr_cols = ELEMENTS + ['ColdWork', 'RecrystT', 'HoldTime', 'GrainSize', 'd_inv_sqrt',
                         'delta', 'VEC', 'dH_mix', 'dS_mix', 'delta_chi', 'Phi_VLC',
                         'eps_Labusch', 'mu_bar', 'Tm_bar', 'HV', 'YS']
corr_matrix = df[corr_cols].corr()

# Top correlations with HV
print("\nTop correlations with Hardness (HV):")
hv_corr = corr_matrix['HV'].drop(['HV', 'YS']).sort_values(key=abs, ascending=False)
for feat, val in hv_corr.head(10).items():
    print(f"  {feat:15s}: {val:+.3f}")

# Top correlations with YS
print("\nTop correlations with Yield Strength (YS):")
ys_corr = corr_matrix['YS'].drop(['HV', 'YS']).sort_values(key=abs, ascending=False)
for feat, val in ys_corr.head(10).items():
    print(f"  {feat:15s}: {val:+.3f}")

# Plot correlation heatmap
fig, ax = plt.subplots(figsize=(16, 14))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
            center=0, vmin=-1, vmax=1, ax=ax, annot_kws={'size': 7})
ax.set_title('Correlation Matrix: Composition, Processing, Descriptors & Properties', fontsize=14)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/01_correlation_matrix.png', dpi=150)
plt.close()

# ============================================================
# 3. HALL-PETCH ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("3. HALL-PETCH ANALYSIS")
print("=" * 70)

df_ys = df.dropna(subset=['YS'])

# --- Fit HV vs d^(-1/2) ---
X_hp = df['d_inv_sqrt'].values.reshape(-1, 1)
y_hv = df['HV'].values
reg_hv = LinearRegression().fit(X_hp, y_hv)
r2_hv = reg_hv.score(X_hp, y_hv)
H0 = reg_hv.intercept_
k_H = reg_hv.coef_[0]

print(f"\nHall-Petch (HV): HV = {H0:.1f} + {k_H:.1f} * d^(-1/2)")
print(f"  R² = {r2_hv:.4f}")

# --- Fit YS vs d^(-1/2) ---
X_hp_ys = df_ys['d_inv_sqrt'].values.reshape(-1, 1)
y_ys = df_ys['YS'].values
reg_ys = LinearRegression().fit(X_hp_ys, y_ys)
r2_ys = reg_ys.score(X_hp_ys, y_ys)
sigma0 = reg_ys.intercept_
k_HP = reg_ys.coef_[0]

print(f"\nHall-Petch (YS): σ_y = {sigma0:.1f} + {k_HP:.1f} * d^(-1/2)")
print(f"  R² = {r2_ys:.4f}")

# Tabor conversion check
df_both = df.dropna(subset=['YS'])
tabor_C = (df_both['HV'] * 9.807) / df_both['YS']
print(f"\nTabor factor HV*9.807/YS: mean={tabor_C.mean():.2f}, std={tabor_C.std():.2f}, "
      f"median={tabor_C.median():.2f}")

# --- Hall-Petch plots ---
batch_colors = {'BBA': '#D55E00', 'BBB': '#0072B2', 'BBC': '#009E73',
                'CBA': '#CC79A7', 'CBB': '#E69F00', 'CBC': '#56B4E9'}

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# YS vs d^(-1/2)
ax = axes[0]
for batch, color in batch_colors.items():
    mask = (df_ys['Iteration'] == batch)
    ax.scatter(df_ys.loc[mask, 'd_inv_sqrt'], df_ys.loc[mask, 'YS'],
               c=color, label=batch, s=50, alpha=0.8, edgecolors='k', linewidth=0.5)
x_fit = np.linspace(df['d_inv_sqrt'].min(), df['d_inv_sqrt'].max(), 100)
ax.plot(x_fit, sigma0 + k_HP * x_fit, 'k--', linewidth=2,
        label=f'σ₀={sigma0:.0f} + {k_HP:.0f}·d⁻¹/² (R²={r2_ys:.3f})')
ax.set_xlabel('d⁻¹/² (µm⁻¹/²)', fontsize=12)
ax.set_ylabel('Yield Strength (MPa)', fontsize=12)
ax.set_title('Hall-Petch: Yield Strength', fontsize=14)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# HV vs d^(-1/2)
ax = axes[1]
for batch, color in batch_colors.items():
    mask = (df['Iteration'] == batch)
    ax.scatter(df.loc[mask, 'd_inv_sqrt'], df.loc[mask, 'HV'],
               c=color, label=batch, s=50, alpha=0.8, edgecolors='k', linewidth=0.5)
ax.plot(x_fit, H0 + k_H * x_fit, 'k--', linewidth=2,
        label=f'H₀={H0:.0f} + {k_H:.0f}·d⁻¹/² (R²={r2_hv:.3f})')
ax.set_xlabel('d⁻¹/² (µm⁻¹/²)', fontsize=12)
ax.set_ylabel('Hardness (HV)', fontsize=12)
ax.set_title('Hall-Petch: Hardness', fontsize=14)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/02_hall_petch.png', dpi=150)
plt.close()

# ============================================================
# 4. COMPOSITION EFFECTS
# ============================================================
print("\n" + "=" * 70)
print("4. COMPOSITION EFFECTS")
print("=" * 70)

# Scatter: YS vs each element
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
for idx, el in enumerate(ELEMENTS):
    ax = axes[idx // 4, idx % 4]
    for batch, color in batch_colors.items():
        mask = (df_ys['Iteration'] == batch)
        ax.scatter(df_ys.loc[mask, el], df_ys.loc[mask, 'YS'],
                   c=color, label=batch if idx == 0 else '', s=30, alpha=0.7)
    r_val, p_val = stats.pearsonr(df_ys[el], df_ys['YS'])
    ax.set_xlabel(f'{el} (at%)', fontsize=11)
    ax.set_ylabel('YS (MPa)' if idx % 4 == 0 else '', fontsize=11)
    ax.set_title(f'{el}: r={r_val:.3f} (p={p_val:.3f})', fontsize=11)
    ax.grid(True, alpha=0.3)
if axes[0, 0].get_legend_handles_labels()[1]:
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc='upper center', ncol=6, fontsize=10)
plt.suptitle('Yield Strength vs. Element Concentration', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/03_YS_vs_composition.png', dpi=150, bbox_inches='tight')
plt.close()

# Scatter: HV vs each element
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
for idx, el in enumerate(ELEMENTS):
    ax = axes[idx // 4, idx % 4]
    for batch, color in batch_colors.items():
        mask = (df['Iteration'] == batch)
        ax.scatter(df.loc[mask, el], df.loc[mask, 'HV'],
                   c=color, label=batch if idx == 0 else '', s=30, alpha=0.7)
    r_val, p_val = stats.pearsonr(df[el], df['HV'])
    ax.set_xlabel(f'{el} (at%)', fontsize=11)
    ax.set_ylabel('HV' if idx % 4 == 0 else '', fontsize=11)
    ax.set_title(f'{el}: r={r_val:.3f} (p={p_val:.3f})', fontsize=11)
    ax.grid(True, alpha=0.3)
plt.suptitle('Hardness vs. Element Concentration', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/04_HV_vs_composition.png', dpi=150, bbox_inches='tight')
plt.close()

# Partial correlations: element with YS controlling for grain size
print("\nPartial correlations (element → YS | grain size):")
from sklearn.linear_model import LinearRegression as LR

for el in ELEMENTS:
    # Residualize both YS and element on d^(-1/2)
    mask = df_ys[el].notna() & df_ys['YS'].notna()
    X_gs = df_ys.loc[mask, 'd_inv_sqrt'].values.reshape(-1, 1)

    resid_ys = df_ys.loc[mask, 'YS'].values - LR().fit(X_gs, df_ys.loc[mask, 'YS'].values).predict(X_gs)
    resid_el = df_ys.loc[mask, el].values - LR().fit(X_gs, df_ys.loc[mask, el].values).predict(X_gs)

    r_partial, p_partial = stats.pearsonr(resid_el, resid_ys)
    print(f"  {el:2s}: r_partial = {r_partial:+.3f} (p={p_partial:.4f})")

# ============================================================
# 5. PROCESSING EFFECTS
# ============================================================
print("\n" + "=" * 70)
print("5. PROCESSING EFFECTS")
print("=" * 70)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Box plot: grain size by cold work
ax = axes[0]
cw_groups = df.groupby('ColdWork')['GrainSize']
positions = sorted(df['ColdWork'].unique())
data_cw = [df[df['ColdWork'] == cw]['GrainSize'].values for cw in positions]
ax.boxplot(data_cw, positions=range(len(positions)), labels=[str(x) for x in positions])
ax.set_xlabel('Cold Work (% Reduction)', fontsize=12)
ax.set_ylabel('Grain Size (µm)', fontsize=12)
ax.set_title('Grain Size vs. Cold Work', fontsize=13)
ax.grid(True, alpha=0.3)

# Scatter: grain size vs recrystallization T, colored by hold time
ax = axes[1]
ht_cmap = plt.cm.viridis
ht_vals = df['HoldTime'].values
sc = ax.scatter(df['RecrystT'], df['GrainSize'], c=np.log10(ht_vals),
                cmap=ht_cmap, s=50, alpha=0.8, edgecolors='k', linewidth=0.5)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('log₁₀(Hold Time, h)', fontsize=10)
ax.set_xlabel('Recrystallization T (°C)', fontsize=12)
ax.set_ylabel('Grain Size (µm)', fontsize=12)
ax.set_title('Grain Size vs. Recryst. Temperature', fontsize=13)
ax.grid(True, alpha=0.3)

# Scatter: grain size vs hold time, colored by T
ax = axes[2]
sc2 = ax.scatter(df['HoldTime'], df['GrainSize'], c=df['RecrystT'],
                 cmap='hot', s=50, alpha=0.8, edgecolors='k', linewidth=0.5)
cbar2 = plt.colorbar(sc2, ax=ax)
cbar2.set_label('Recryst. T (°C)', fontsize=10)
ax.set_xlabel('Hold Time (h)', fontsize=12)
ax.set_ylabel('Grain Size (µm)', fontsize=12)
ax.set_title('Grain Size vs. Hold Time', fontsize=13)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/05_processing_effects.png', dpi=150)
plt.close()

# Correlations with grain size
print("\nCorrelations with Grain Size:")
for feat in ['ColdWork', 'RecrystT', 'HoldTime']:
    r, p = stats.pearsonr(df[feat], df['GrainSize'])
    print(f"  {feat:15s}: r={r:+.3f} (p={p:.4f})")

# ============================================================
# 6. DESCRIPTOR ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("6. HEA DESCRIPTOR ANALYSIS")
print("=" * 70)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
desc_feats = ['delta', 'VEC', 'dH_mix', 'Phi_VLC', 'eps_Labusch', 'dS_mix']
for idx, feat in enumerate(desc_feats):
    ax = axes[idx // 3, idx % 3]
    for batch, color in batch_colors.items():
        mask = (df_ys['Iteration'] == batch)
        ax.scatter(df_ys.loc[mask, feat], df_ys.loc[mask, 'YS'],
                   c=color, label=batch, s=40, alpha=0.7)
    r_val, p_val = stats.pearsonr(df_ys[feat].replace([np.inf, -np.inf], np.nan).dropna(),
                                   df_ys.loc[df_ys[feat].replace([np.inf, -np.inf], np.nan).notna(), 'YS'])
    ax.set_xlabel(feat, fontsize=12)
    ax.set_ylabel('YS (MPa)', fontsize=12)
    ax.set_title(f'{feat}: r={r_val:.3f} (p={p_val:.3f})', fontsize=12)
    ax.grid(True, alpha=0.3)
    if idx == 0:
        ax.legend(fontsize=8)
plt.suptitle('Yield Strength vs. HEA Descriptors', fontsize=14)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/06_YS_vs_descriptors.png', dpi=150)
plt.close()

# ============================================================
# 7. MULTIVARIATE LINEAR REGRESSION (OLS with statsmodels)
# ============================================================
print("\n" + "=" * 70)
print("7. MULTIVARIATE LINEAR REGRESSION")
print("=" * 70)

# --- YS model ---
print("\n--- Model A: YS ~ compositions + d^(-1/2) + processing ---")
features_A = ELEMENTS + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime']
df_model = df_ys[features_A + ['YS']].dropna()
X_ols = sm.add_constant(df_model[features_A])
model_ys = sm.OLS(df_model['YS'], X_ols).fit()
print(model_ys.summary())

# --- HV model ---
print("\n--- Model B: HV ~ compositions + d^(-1/2) + processing ---")
df_model_hv = df[features_A + ['HV']].dropna()
X_ols_hv = sm.add_constant(df_model_hv[features_A])
model_hv = sm.OLS(df_model_hv['HV'], X_ols_hv).fit()
print(model_hv.summary())

# --- YS with descriptors ---
print("\n--- Model C: YS ~ delta + VEC + dH_mix + Phi_VLC + d^(-1/2) + ColdWork + RecrystT + HoldTime ---")
features_C = ['delta', 'VEC', 'dH_mix', 'Phi_VLC', 'd_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime']
df_model_C = df_ys[features_C + ['YS']].replace([np.inf, -np.inf], np.nan).dropna()
X_ols_C = sm.add_constant(df_model_C[features_C])
model_ys_C = sm.OLS(df_model_C['YS'], X_ols_C).fit()
print(model_ys_C.summary())

# ============================================================
# 8. ADVANCED MODEL COMPARISON
# ============================================================
print("\n" + "=" * 70)
print("8. ADVANCED MODEL COMPARISON (Cross-Validated)")
print("=" * 70)

# Prepare data — use compositions + d^(-1/2) + processing
feature_sets = {
    'Compositions+HP+Process': ELEMENTS + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime'],
    'Descriptors+HP+Process': ['delta', 'VEC', 'dH_mix', 'eps_Labusch', 'd_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime'],
    'Combined': ELEMENTS + ['delta', 'VEC', 'dH_mix', 'd_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime'],
}

targets = {'YS': df_ys, 'HV': df}

for target_name, df_target in targets.items():
    print(f"\n{'=' * 50}")
    print(f"TARGET: {target_name}")
    print(f"{'=' * 50}")

    for feat_name, features in feature_sets.items():
        df_clean = df_target[features + [target_name]].replace([np.inf, -np.inf], np.nan).dropna()
        X = df_clean[features].values
        y = df_clean[target_name].values
        n = len(y)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        cv = RepeatedKFold(n_splits=5, n_repeats=10, random_state=42)
        loo = LeaveOneOut()

        models = {
            'OLS': LinearRegression(),
            'Ridge': Ridge(alpha=1.0),
            'Lasso': Lasso(alpha=0.5, max_iter=10000),
            'ElasticNet': ElasticNet(alpha=0.5, l1_ratio=0.5, max_iter=10000),
            'Random Forest': RandomForestRegressor(n_estimators=200, max_depth=5, min_samples_leaf=5, random_state=42),
            'Gradient Boost': GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05,
                                                        min_samples_leaf=5, random_state=42),
        }

        print(f"\n  Feature set: {feat_name} ({len(features)} features, n={n})")
        print(f"  {'Model':<18s} {'5-Fold R² (mean±std)':>22s} {'LOO R²':>10s} {'LOO RMSE':>10s} {'LOO MAE':>10s}")
        print(f"  {'-' * 72}")

        for mname, model in models.items():
            # 5-fold repeated CV
            scores_5f = cross_val_score(model, X_scaled, y, cv=cv, scoring='r2')

            # LOO CV
            loo_preds = np.zeros(n)
            for train_idx, test_idx in loo.split(X_scaled):
                model.fit(X_scaled[train_idx], y[train_idx])
                loo_preds[test_idx] = model.predict(X_scaled[test_idx])

            r2_loo = r2_score(y, loo_preds)
            rmse_loo = np.sqrt(mean_squared_error(y, loo_preds))
            mae_loo = mean_absolute_error(y, loo_preds)

            print(f"  {mname:<18s} {scores_5f.mean():>8.4f} ± {scores_5f.std():.4f}     "
                  f"{r2_loo:>8.4f}  {rmse_loo:>8.2f}  {mae_loo:>8.2f}")

# ============================================================
# 9. BEST MODEL DEEP DIVE — Gradient Boosting with SHAP-like Analysis
# ============================================================
print("\n" + "=" * 70)
print("9. BEST MODEL DEEP DIVE: Feature Importance")
print("=" * 70)

for target_name, df_target in targets.items():
    features = ELEMENTS + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime']
    df_clean = df_target[features + [target_name]].dropna()
    X = df_clean[features].values
    y = df_clean[target_name].values

    gb = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05,
                                    min_samples_leaf=5, random_state=42)
    gb.fit(X, y)
    imp = pd.Series(gb.feature_importances_, index=features).sort_values(ascending=True)

    print(f"\n  {target_name} — Gradient Boosting Feature Importance:")
    for feat, val in imp.items():
        bar = '█' * int(val * 50)
        print(f"    {feat:15s}: {val:.4f} {bar}")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    imp.plot.barh(ax=ax, color='steelblue')
    ax.set_xlabel('Feature Importance', fontsize=12)
    ax.set_title(f'Gradient Boosting Feature Importance — {target_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'{PLOT_DIR}/07_feature_importance_{target_name}.png', dpi=150)
    plt.close()

# ============================================================
# 10. PARITY PLOTS (Best model LOO predictions)
# ============================================================
print("\n" + "=" * 70)
print("10. PARITY PLOTS")
print("=" * 70)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

for idx, (target_name, df_target) in enumerate(targets.items()):
    features = ELEMENTS + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime']
    df_clean = df_target[features + [target_name]].dropna()
    X = df_clean[features].values
    y = df_clean[target_name].values
    n = len(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    gb = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05,
                                    min_samples_leaf=5, random_state=42)

    loo_preds = np.zeros(n)
    for train_idx, test_idx in LeaveOneOut().split(X_scaled):
        gb.fit(X_scaled[train_idx], y[train_idx])
        loo_preds[test_idx] = gb.predict(X_scaled[test_idx])

    r2 = r2_score(y, loo_preds)
    rmse = np.sqrt(mean_squared_error(y, loo_preds))

    ax = axes[idx]
    for batch, color in batch_colors.items():
        mask = (df_clean.merge(df_target[['Alloy', 'Iteration']], left_index=True, right_index=True)['Iteration'] == batch).values
        if mask.sum() > 0:
            ax.scatter(y[mask], loo_preds[mask], c=color, label=batch, s=40, alpha=0.8, edgecolors='k', linewidth=0.5)

    lims = [min(y.min(), loo_preds.min()) * 0.9, max(y.max(), loo_preds.max()) * 1.1]
    ax.plot(lims, lims, 'k--', linewidth=1.5, alpha=0.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel(f'Experimental {target_name}', fontsize=12)
    ax.set_ylabel(f'Predicted {target_name} (LOO)', fontsize=12)
    ax.set_title(f'{target_name}: R²={r2:.3f}, RMSE={rmse:.1f}', fontsize=13)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/08_parity_plots.png', dpi=150)
plt.close()

# ============================================================
# 11. BATCH-SPECIFIC HALL-PETCH (per iteration)
# ============================================================
print("\n" + "=" * 70)
print("11. BATCH-SPECIFIC HALL-PETCH ANALYSIS")
print("=" * 70)

print(f"\n  {'Batch':6s} {'n':>4s} {'σ₀ (MPa)':>10s} {'k_HP':>10s} {'R² (YS)':>8s}  |  {'H₀ (HV)':>8s} {'k_H':>8s} {'R² (HV)':>8s}")
print(f"  {'-' * 75}")

fig, axes = plt.subplots(2, 3, figsize=(18, 12))

for idx, batch in enumerate(sorted(df['Iteration'].unique())):
    df_b = df[df['Iteration'] == batch]
    df_b_ys = df_b.dropna(subset=['YS'])

    ax = axes[idx // 3, idx % 3]

    # HV fit
    if len(df_b) >= 3:
        X_b = df_b['d_inv_sqrt'].values.reshape(-1, 1)
        reg_b_hv = LinearRegression().fit(X_b, df_b['HV'].values)
        r2_b_hv = reg_b_hv.score(X_b, df_b['HV'].values)
        H0_b = reg_b_hv.intercept_
        kH_b = reg_b_hv.coef_[0]
    else:
        H0_b = kH_b = r2_b_hv = np.nan

    # YS fit
    if len(df_b_ys) >= 3:
        X_b_ys = df_b_ys['d_inv_sqrt'].values.reshape(-1, 1)
        reg_b_ys = LinearRegression().fit(X_b_ys, df_b_ys['YS'].values)
        r2_b_ys = reg_b_ys.score(X_b_ys, df_b_ys['YS'].values)
        s0_b = reg_b_ys.intercept_
        kHP_b = reg_b_ys.coef_[0]
    else:
        s0_b = kHP_b = r2_b_ys = np.nan

    print(f"  {batch:6s} {len(df_b_ys):>4d} {s0_b:>10.1f} {kHP_b:>10.1f} {r2_b_ys:>8.3f}  |  "
          f"{H0_b:>8.1f} {kH_b:>8.1f} {r2_b_hv:>8.3f}")

    # Plot per-batch
    ax.scatter(df_b['d_inv_sqrt'], df_b['HV'], c='steelblue', label='HV', s=50, alpha=0.8)
    if len(df_b_ys) > 0:
        ax.scatter(df_b_ys['d_inv_sqrt'], df_b_ys['YS'], c='coral', marker='s', label='YS', s=50, alpha=0.8)
    x_range = np.linspace(df_b['d_inv_sqrt'].min() * 0.9, df_b['d_inv_sqrt'].max() * 1.1, 50)
    if not np.isnan(H0_b):
        ax.plot(x_range, H0_b + kH_b * x_range, 'b--', alpha=0.7)
    if not np.isnan(s0_b):
        ax.plot(x_range, s0_b + kHP_b * x_range, 'r--', alpha=0.7)
    ax.set_xlabel('d⁻¹/² (µm⁻¹/²)', fontsize=11)
    ax.set_ylabel('HV / YS (MPa)', fontsize=11)
    ax.set_title(f'{batch} (n={len(df_b)})', fontsize=12)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.suptitle('Batch-Specific Hall-Petch Analysis', fontsize=14)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/09_batch_hall_petch.png', dpi=150)
plt.close()

# ============================================================
# 12. PHYSICS-INFORMED MODEL: σ₀(composition) + k_HP·d^(-1/2)
# ============================================================
print("\n" + "=" * 70)
print("12. PHYSICS-INFORMED MODEL: σ₀(comp) + k_HP·d^(-1/2)")
print("=" * 70)

# Model: YS = [a0 + a1*delta + a2*VEC + a3*dH_mix + a4*eps_L] + [b0 + b1*delta]*d^(-1/2)
# This separates composition-dependent intrinsic strength from composition-dependent HP slope

df_pi = df_ys[['YS', 'delta', 'VEC', 'dH_mix', 'eps_Labusch', 'd_inv_sqrt',
               'ColdWork', 'RecrystT', 'HoldTime'] + ELEMENTS].replace([np.inf, -np.inf], np.nan).dropna()

# Build interaction features
df_pi['delta_x_dinv'] = df_pi['delta'] * df_pi['d_inv_sqrt']
df_pi['VEC_x_dinv'] = df_pi['VEC'] * df_pi['d_inv_sqrt']

features_pi = ['delta', 'VEC', 'dH_mix', 'eps_Labusch', 'd_inv_sqrt',
               'delta_x_dinv', 'VEC_x_dinv', 'ColdWork', 'RecrystT', 'HoldTime']

X_pi = sm.add_constant(df_pi[features_pi])
model_pi = sm.OLS(df_pi['YS'], X_pi).fit()
print(model_pi.summary())

# LOO cross-validation of physics-informed model
X_pi_arr = df_pi[features_pi].values
y_pi = df_pi['YS'].values
scaler_pi = StandardScaler()
X_pi_scaled = scaler_pi.fit_transform(X_pi_arr)

loo_preds_pi = np.zeros(len(y_pi))
for train_idx, test_idx in LeaveOneOut().split(X_pi_scaled):
    lr = LinearRegression().fit(X_pi_scaled[train_idx], y_pi[train_idx])
    loo_preds_pi[test_idx] = lr.predict(X_pi_scaled[test_idx])

r2_pi_loo = r2_score(y_pi, loo_preds_pi)
rmse_pi_loo = np.sqrt(mean_squared_error(y_pi, loo_preds_pi))
print(f"\nPhysics-informed model LOO: R²={r2_pi_loo:.4f}, RMSE={rmse_pi_loo:.2f} MPa")

# ============================================================
# 13. GAUSSIAN PROCESS REGRESSION (with uncertainty)
# ============================================================
print("\n" + "=" * 70)
print("13. GAUSSIAN PROCESS REGRESSION")
print("=" * 70)

for target_name, df_target in targets.items():
    features = ELEMENTS + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime']
    df_clean = df_target[features + [target_name]].dropna()
    X = df_clean[features].values
    y = df_clean[target_name].values
    n = len(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    kernel = ConstantKernel(1.0) * Matern(length_scale=np.ones(X.shape[1]), nu=2.5) + WhiteKernel(noise_level=1.0)
    gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10, random_state=42)

    # LOO with uncertainty
    loo_preds_gp = np.zeros(n)
    loo_stds_gp = np.zeros(n)
    for train_idx, test_idx in LeaveOneOut().split(X_scaled):
        gpr.fit(X_scaled[train_idx], y[train_idx])
        pred, std = gpr.predict(X_scaled[test_idx], return_std=True)
        loo_preds_gp[test_idx] = pred
        loo_stds_gp[test_idx] = std

    r2_gp = r2_score(y, loo_preds_gp)
    rmse_gp = np.sqrt(mean_squared_error(y, loo_preds_gp))
    print(f"\n  {target_name} GPR LOO: R²={r2_gp:.4f}, RMSE={rmse_gp:.2f}")
    print(f"  Mean prediction uncertainty (1σ): {loo_stds_gp.mean():.2f}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nPlots saved to: {PLOT_DIR}/")
print(f"Augmented data: {DATA_DIR}/data_with_descriptors.csv")
print(f"\nKey findings:")
print(f"  - Simple Hall-Petch R² (YS): {r2_ys:.3f}")
print(f"  - Simple Hall-Petch R² (HV): {r2_hv:.3f}")
print(f"  - σ₀ = {sigma0:.1f} MPa, k_HP = {k_HP:.1f} MPa·µm^(1/2)")
print(f"  - H₀ = {H0:.1f} HV, k_H = {k_H:.1f} HV·µm^(1/2)")
print(f"  - Tabor factor: {tabor_C.mean():.2f} ± {tabor_C.std():.2f}")
print(f"  - Best linear model: see OLS summaries above")
print(f"  - Best ML model: see cross-validation table above")
