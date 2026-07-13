#!/usr/bin/env python3
"""
Hardness Analysis: Tabor Relation, HV Hall–Petch, and Composition Models
=========================================================================
Sections:
  A. Tabor relation: C_eff = HV_MPa / YS, composition & GS dependence
  B. Hall–Petch scaling laws for HV (8 alternatives + optimized exponent)
  C. Composition-dependent H₀ models (M0–M10 hierarchy)
  D. Joint HV–YS analysis & literature context
  E. Rank correlation analysis: HV vs YS rankings and Simpson's paradox

Outputs:
  - Figures 50–56 in analysis_plots/
  - hardness_scaling_comparison.csv
  - hardness_model_comparison.csv
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut, LeaveOneGroupOut

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/ (for _config)
from _config import REPO_ROOT, DATA_DIR, RAW_DATA_DIR, RESULTS_DIR, PLOTS_DIR, PAPER_DIR, PAPER_FIG_DIR
BASE = str(REPO_ROOT)
PLOT_DIR = f'{PLOTS_DIR}'
BATCH_COLORS = {'BBA': '#E74C3C', 'BBB': '#3498DB', 'BBC': '#2ECC71',
                'CBA': '#9B59B6', 'CBB': '#F39C12', 'CBC': '#1ABC9C'}

plt.rcParams.update({'font.size': 11, 'font.family': 'serif'})

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def compute_ic(y_true, y_pred, k, n):
    """Compute AIC, AICc, BIC."""
    rss = np.sum((y_true - y_pred) ** 2)
    if rss <= 0:
        rss = 1e-15
    log_term = n * np.log(rss / n)
    aic = log_term + 2 * k
    bic = log_term + k * np.log(n)
    if n - k - 1 > 0:
        aicc = aic + 2 * k * (k + 1) / (n - k - 1)
    else:
        aicc = np.inf
    return {'AIC': aic, 'AICc': aicc, 'BIC': bic, 'RSS': rss}


def ols_loo(X, y):
    """Analytical LOO via hat matrix for OLS. Returns dict of metrics."""
    n = len(y)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    y_pred = X @ beta
    resid = y - y_pred

    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2_train = 1 - ss_res / ss_tot

    H = X @ np.linalg.solve(X.T @ X, X.T)
    h_ii = np.diag(H)
    loo_resid = resid / (1 - h_ii)
    ss_loo = np.sum(loo_resid ** 2)
    r2_loo = 1 - ss_loo / ss_tot
    loo_rmse = np.sqrt(ss_loo / n)

    k_params = X.shape[1] + 1  # +1 for noise variance
    ic = compute_ic(y, y_pred, k_params, n)

    return {
        'beta': beta, 'y_pred': y_pred,
        'loo_pred': y - loo_resid,
        'r2_train': r2_train, 'r2_loo': r2_loo,
        'loo_rmse': loo_rmse, 'k_params': k_params,
        'bic': ic['BIC'], 'aic': ic['AIC'], 'aicc': ic['AICc'],
    }


# ============================================================
# 1. LOAD DATA
# ============================================================
print("=" * 70)
print("HARDNESS ANALYSIS: TABOR, HV HALL–PETCH, COMPOSITION MODELS")
print("=" * 70)

df = pd.read_csv(f'{DATA_DIR}/data_with_descriptors.csv')

# HV is available for all alloys; YS may have NaN for 1 alloy
n_all = len(df)
print(f"\nTotal alloys: {n_all}")
print(f"  with HV: {df['HV'].notna().sum()}")
print(f"  with YS: {df['YS'].notna().sum()}")

# For Tabor analysis: need both HV and YS
df_both = df.dropna(subset=['HV', 'YS']).copy()
n_both = len(df_both)

# For HV-only analysis: need HV
df_hv = df.dropna(subset=['HV']).copy()
n_hv = len(df_hv)

# Extract arrays
hv_both = df_both['HV'].values.astype(float)
ys_both = df_both['YS'].values.astype(float)
d_both = df_both['GrainSize'].values.astype(float)
d_inv_sqrt_both = d_both ** -0.5
batches_both = df_both['Iteration'].values

hv = df_hv['HV'].values.astype(float)
d_hv = df_hv['GrainSize'].values.astype(float)
d_inv_sqrt_hv = d_hv ** -0.5
batches_hv = df_hv['Iteration'].values

elem_names = ['Al_frac', 'Co_frac', 'Cr_frac', 'Cu_frac', 'Fe_frac', 'Mn_frac', 'V_frac']
elem_short = ['Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'V']
X_elem_both = df_both[elem_names].values.astype(float)
X_elem_hv = df_hv[elem_names].values.astype(float)

V_both = df_both['V_frac'].values.astype(float)
V_hv = df_hv['V_frac'].values.astype(float)
Mn_hv = df_hv['Mn_frac'].values.astype(float)
Al_hv = df_hv['Al_frac'].values.astype(float)

print(f"\nHV range: {hv.min():.1f}–{hv.max():.1f}")
print(f"YS range (with HV): {ys_both.min():.0f}–{ys_both.max():.0f} MPa")
print(f"GS range: {d_hv.min():.0f}–{d_hv.max():.0f} µm")


# ============================================================
# SECTION A: TABOR RELATION  (Figures 50–51)
# ============================================================
print("\n" + "=" * 70)
print("SECTION A: TABOR RELATION (HV vs YS)")
print("=" * 70)

# Convert HV to MPa: HV_MPa = HV × 9.807
HV_MPa = hv_both * 9.807
C_eff = HV_MPa / ys_both

print(f"\n  C_eff = HV_MPa / YS")
print(f"  Mean:   {C_eff.mean():.2f}")
print(f"  Std:    {C_eff.std():.2f}")
print(f"  Median: {np.median(C_eff):.2f}")
print(f"  Range:  {C_eff.min():.2f}–{C_eff.max():.2f}")
print(f"  95% CI: [{np.percentile(C_eff, 2.5):.2f}, {np.percentile(C_eff, 97.5):.2f}]")

# t-test: C_eff != 3
t_stat, p_val = stats.ttest_1samp(C_eff, 3.0)
print(f"\n  t-test H₀: C_eff = 3.0")
print(f"  t = {t_stat:.2f}, p = {p_val:.4f}")
if p_val < 0.05:
    print(f"  → C_eff significantly differs from 3 (p < 0.05)")
else:
    print(f"  → Cannot reject C_eff = 3")

# Inferred UTS/YS ratio
UTS_inferred = HV_MPa / 3.0  # σ_UTS ≈ HV_MPa / 3
UTS_YS_ratio = UTS_inferred / ys_both
print(f"\n  Inferred UTS/YS ratio (assuming HV ≈ 3·σ_UTS):")
print(f"  Mean:   {UTS_YS_ratio.mean():.2f}")
print(f"  Range:  {UTS_YS_ratio.min():.2f}–{UTS_YS_ratio.max():.2f}")

# OLS: C_eff = γ₀ + Σγᵢ·xᵢ
print("\n  Composition dependence of C_eff (OLS):")
ones_both = np.ones(n_both)
X_c = np.column_stack([ones_both, X_elem_both])
beta_c = np.linalg.lstsq(X_c, C_eff, rcond=None)[0]
C_pred = X_c @ beta_c
ss_res_c = np.sum((C_eff - C_pred) ** 2)
ss_tot_c = np.sum((C_eff - C_eff.mean()) ** 2)
r2_c = 1 - ss_res_c / ss_tot_c
print(f"  R² = {r2_c:.3f}")

# Per-element correlations
print(f"\n  {'Element':>8s} {'r':>8s} {'p':>10s}")
print("  " + "-" * 30)
elem_corrs = []
for i, elem in enumerate(elem_short):
    r, p = stats.pearsonr(X_elem_both[:, i], C_eff)
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    print(f"  {elem:>8s} {r:>8.3f} {p:>10.4f} {sig}")
    elem_corrs.append((elem, r, p))

# C_eff vs grain size
r_cd, p_cd = stats.pearsonr(d_inv_sqrt_both, C_eff)
print(f"\n  C_eff vs d^(-1/2): r = {r_cd:.3f}, p = {p_cd:.4f}")

# ANOVA: C_eff across batches
batch_groups = [C_eff[batches_both == b] for b in sorted(set(batches_both))]
f_stat, p_anova = stats.f_oneway(*batch_groups)
print(f"  ANOVA C_eff across batches: F = {f_stat:.2f}, p = {p_anova:.4f}")

# ---- FIGURE 50: Tabor relation 2×2 ----
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# (a) HV_MPa vs YS
ax = axes[0, 0]
for batch in sorted(set(batches_both)):
    mask = batches_both == batch
    ax.scatter(ys_both[mask], HV_MPa[mask], c=BATCH_COLORS.get(batch, 'gray'),
               label=batch, s=40, alpha=0.7, edgecolors='k', linewidths=0.3)
ys_range = np.linspace(ys_both.min() * 0.9, ys_both.max() * 1.1, 100)
ax.plot(ys_range, 3.0 * ys_range, 'k--', linewidth=1.5, label='C = 3 (Tabor)')
slope_fit, intercept_fit, r_fit, p_fit, se_fit = stats.linregress(ys_both, HV_MPa)
ax.plot(ys_range, intercept_fit + slope_fit * ys_range, 'r-', linewidth=2,
        label=f'Best fit (C = {slope_fit:.2f})')
ax.set_xlabel('Yield Strength (MPa)')
ax.set_ylabel('HV (MPa)')
ax.set_title('(a) Tabor Relation: HV vs YS')
ax.legend(fontsize=8, ncol=2)

# (b) Histogram of C_eff
ax = axes[0, 1]
ax.hist(C_eff, bins=20, color='steelblue', edgecolor='k', alpha=0.7, density=True)
ax.axvline(x=3.0, color='red', linestyle='--', linewidth=2, label='C = 3 (Tabor)')
ax.axvline(x=C_eff.mean(), color='orange', linestyle='-', linewidth=2,
           label=f'Mean = {C_eff.mean():.2f}')
ax.set_xlabel('C_eff = HV_MPa / YS')
ax.set_ylabel('Density')
ax.set_title('(b) Distribution of Effective Tabor Factor')
ax.legend(fontsize=9)

# (c) C_eff vs d^(-1/2) colored by V
ax = axes[1, 0]
sc = ax.scatter(d_inv_sqrt_both, C_eff, c=V_both, cmap='viridis',
                s=40, edgecolors='k', linewidths=0.3)
plt.colorbar(sc, ax=ax, label='V fraction')
if abs(r_cd) > 0.05:
    z = np.polyfit(d_inv_sqrt_both, C_eff, 1)
    ax.plot(np.sort(d_inv_sqrt_both), np.polyval(z, np.sort(d_inv_sqrt_both)),
            'r-', linewidth=1.5)
ax.set_xlabel('d⁻¹/² (µm⁻¹/²)')
ax.set_ylabel('C_eff')
ax.set_title(f'(c) C_eff vs Grain Size (r = {r_cd:.3f})')

# (d) C_eff vs V_frac (strongest element effect)
ax = axes[1, 1]
# Find strongest correlated element
strongest = max(elem_corrs, key=lambda x: abs(x[1]))
strong_idx = elem_short.index(strongest[0])
x_strong = X_elem_both[:, strong_idx]
r_strong = strongest[1]
ax.scatter(x_strong, C_eff, c='steelblue', s=40, edgecolors='k', linewidths=0.3)
z = np.polyfit(x_strong, C_eff, 1)
x_sort = np.sort(x_strong)
ax.plot(x_sort, np.polyval(z, x_sort), 'r-', linewidth=1.5)
ax.set_xlabel(f'{strongest[0]} fraction')
ax.set_ylabel('C_eff')
ax.set_title(f'(d) C_eff vs {strongest[0]} (r = {r_strong:.3f}, p = {strongest[2]:.4f})')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/50_tabor_relation.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 50_tabor_relation.png")

# ---- FIGURE 51: C_eff vs each element (2×4 panel) ----
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes_flat = axes.flatten()

for i, elem in enumerate(elem_short):
    ax = axes_flat[i]
    x = X_elem_both[:, i]
    r, p = stats.pearsonr(x, C_eff)
    ax.scatter(x, C_eff, c='steelblue', s=25, alpha=0.6, edgecolors='k', linewidths=0.2)
    if x.std() > 1e-6:
        z = np.polyfit(x, C_eff, 1)
        x_sort = np.sort(x)
        ax.plot(x_sort, np.polyval(z, x_sort), 'r-', linewidth=1.5)
    ax.set_xlabel(f'{elem} fraction')
    ax.set_ylabel('C_eff')
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    ax.set_title(f'{elem}: r = {r:.3f} ({sig})')
    ax.axhline(y=3.0, color='gray', linestyle='--', linewidth=0.8)

# Hide last subplot (8th element = Ni as solvent)
ax = axes_flat[7]
# Also show Ni
Ni_both = df_both['Ni_frac'].values.astype(float)
r_ni, p_ni = stats.pearsonr(Ni_both, C_eff)
ax.scatter(Ni_both, C_eff, c='steelblue', s=25, alpha=0.6, edgecolors='k', linewidths=0.2)
z = np.polyfit(Ni_both, C_eff, 1)
ax.plot(np.sort(Ni_both), np.polyval(z, np.sort(Ni_both)), 'r-', linewidth=1.5)
ax.set_xlabel('Ni fraction')
ax.set_ylabel('C_eff')
sig_ni = '***' if p_ni < 0.001 else '**' if p_ni < 0.01 else '*' if p_ni < 0.05 else 'ns'
ax.set_title(f'Ni: r = {r_ni:.3f} ({sig_ni})')
ax.axhline(y=3.0, color='gray', linestyle='--', linewidth=0.8)

plt.suptitle('Composition Dependence of Effective Tabor Factor', fontsize=14, y=1.02)
plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/51_tabor_composition.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"  Saved 51_tabor_composition.png")


# ============================================================
# SECTION B: HALL–PETCH SCALING LAWS FOR HV  (Figure 52)
# ============================================================
print("\n" + "=" * 70)
print("SECTION B: HALL–PETCH SCALING LAWS FOR HV")
print("=" * 70)

n = n_hv
d = d_hv
d_inv_sqrt = d_inv_sqrt_hv
y = hv  # target is now HV (in kgf/mm², i.e., standard Vickers units)
groups = batches_hv
ones = np.ones(n)

# Fit optimal exponent
def neg_r2_hv(exp):
    f = d ** (-exp)
    X_ = np.column_stack([np.ones(n), f])
    beta_ = np.linalg.lstsq(X_, y, rcond=None)[0]
    pred_ = X_ @ beta_
    ss_res_ = np.sum((y - pred_) ** 2)
    ss_tot_ = np.sum((y - y.mean()) ** 2)
    return -(1 - ss_res_ / ss_tot_)

result = minimize_scalar(neg_r2_hv, bounds=(0.01, 2.0), method='bounded')
n_opt_hv = result.x
print(f"\n  Optimal exponent for HV: n = {n_opt_hv:.3f}")

# Define scaling laws
scaling_specs = {
    'd^(-1/2) [Hall-Petch]': d ** (-0.5),
    'd^(-2/3)': d ** (-2.0 / 3.0),
    'd^(-1/3) [Baldwin]': d ** (-1.0 / 3.0),
    'd^(-1) [Dunstan-Bushby]': d ** (-1.0),
    'ln(d)/d [Crit. thickness]': np.log(d) / d,
    'ln(d)': np.log(d),
}

scaling_results = []

for name, feat in scaling_specs.items():
    X_gs = np.column_stack([ones, feat])
    res = ols_loo(X_gs, y)
    scaling_results.append({
        'Scaling': name, 'k': 2,
        'Train_R2': res['r2_train'], 'LOO_R2': res['r2_loo'],
        'LOO_RMSE': res['loo_rmse'],
        'AIC': res['aic'], 'BIC': res['bic'],
        'intercept': res['beta'][0], 'slope': res['beta'][1],
    })

# Composite: d^(-1/2) + d^(-1)
X_comp = np.column_stack([ones, d ** (-0.5), d ** (-1.0)])
res_comp = ols_loo(X_comp, y)
scaling_results.append({
    'Scaling': '1/√d + 1/d [Composite]', 'k': 3,
    'Train_R2': res_comp['r2_train'], 'LOO_R2': res_comp['r2_loo'],
    'LOO_RMSE': res_comp['loo_rmse'],
    'AIC': res_comp['aic'], 'BIC': res_comp['bic'],
    'intercept': res_comp['beta'][0], 'slope': res_comp['beta'][1],
})

# Optimized exponent (3 params)
X_nopt = np.column_stack([ones, d ** (-n_opt_hv)])
res_nopt = ols_loo(X_nopt, y)
ic_nopt3 = compute_ic(y, res_nopt['y_pred'], 3, n)
scaling_results.append({
    'Scaling': f'd^(-{n_opt_hv:.3f}) [Optimized]', 'k': 3,
    'Train_R2': res_nopt['r2_train'], 'LOO_R2': res_nopt['r2_loo'],
    'LOO_RMSE': res_nopt['loo_rmse'],
    'AIC': ic_nopt3['AIC'], 'BIC': ic_nopt3['BIC'],
    'intercept': res_nopt['beta'][0], 'slope': res_nopt['beta'][1],
})

# Sort by BIC
scale_df = pd.DataFrame(scaling_results).sort_values('BIC')
min_bic = scale_df['BIC'].min()
scale_df['ΔBIC'] = scale_df['BIC'] - min_bic

print(f"\n  {'Scaling':<32s} {'k':>2s} {'Train R²':>8s} {'LOO R²':>7s} {'RMSE':>6s} {'BIC':>8s} {'ΔBIC':>6s}")
print(f"  {'-'*80}")
for _, r in scale_df.iterrows():
    support = "strong" if r['ΔBIC'] < 2 else "moderate" if r['ΔBIC'] < 6 else "weak" if r['ΔBIC'] < 10 else "none"
    print(f"  {r['Scaling']:<32s} {r['k']:>2.0f} {r['Train_R2']:>8.4f} {r['LOO_R2']:>7.4f} "
          f"{r['LOO_RMSE']:>6.1f} {r['BIC']:>8.2f} {r['ΔBIC']:>6.1f} ({support})")

# Save scaling comparison
scale_df.to_csv(f'{RESULTS_DIR}/hardness_scaling_comparison.csv', index=False)
print(f"\n  Saved hardness_scaling_comparison.csv")

# Baseline HP fit (for reporting)
X_hp = np.column_stack([ones, d_inv_sqrt])
hp_res = ols_loo(X_hp, y)
H0_global = hp_res['beta'][0]
kH_global = hp_res['beta'][1]
print(f"\n  Baseline HV HP: H₀ = {H0_global:.1f}, k_H = {kH_global:.1f} HV·µm¹/²")
print(f"  k_H in MPa·µm¹/²: {kH_global * 9.807:.0f}")
print(f"  Train R² = {hp_res['r2_train']:.4f}, LOO R² = {hp_res['r2_loo']:.4f}")

# R² vs exponent curve (for comparison with YS)
exponents = np.linspace(0.1, 1.5, 200)
r2_vs_exp_hv = []
for exp in exponents:
    f = d ** (-exp)
    X_ = np.column_stack([ones, f])
    beta_ = np.linalg.lstsq(X_, y, rcond=None)[0]
    pred_ = X_ @ beta_
    ss_res_ = np.sum((y - pred_) ** 2)
    ss_tot_ = np.sum((y - y.mean()) ** 2)
    r2_vs_exp_hv.append(1 - ss_res_ / ss_tot_)

# Also compute for YS (for overlay)
df_ys = df.dropna(subset=['YS']).copy()
y_ys = df_ys['YS'].values.astype(float)
d_ys = df_ys['GrainSize'].values.astype(float)
n_ys = len(y_ys)
r2_vs_exp_ys = []
for exp in exponents:
    f = d_ys ** (-exp)
    X_ = np.column_stack([np.ones(n_ys), f])
    beta_ = np.linalg.lstsq(X_, y_ys, rcond=None)[0]
    pred_ = X_ @ beta_
    ss_res_ = np.sum((y_ys - pred_) ** 2)
    ss_tot_ = np.sum((y_ys - y_ys.mean()) ** 2)
    r2_vs_exp_ys.append(1 - ss_res_ / ss_tot_)

# Optimal exponent for YS (for reference)
def neg_r2_ys(exp):
    f = d_ys ** (-exp)
    X_ = np.column_stack([np.ones(n_ys), f])
    beta_ = np.linalg.lstsq(X_, y_ys, rcond=None)[0]
    pred_ = X_ @ beta_
    ss_r = np.sum((y_ys - pred_) ** 2)
    ss_t = np.sum((y_ys - y_ys.mean()) ** 2)
    return -(1 - ss_r / ss_t)
n_opt_ys = minimize_scalar(neg_r2_ys, bounds=(0.01, 2.0), method='bounded').x
print(f"  Optimal exponent for YS: n = {n_opt_ys:.3f}")

# Per-batch HP fits
batch_hp_results = {}
for batch in sorted(set(groups)):
    mask = groups == batch
    n_b = mask.sum()
    if n_b < 5:
        continue
    y_b = y[mask]
    d_b = d_inv_sqrt[mask]
    X_b = np.column_stack([np.ones(n_b), d_b])
    beta_b = np.linalg.lstsq(X_b, y_b, rcond=None)[0]
    y_pred_b = X_b @ beta_b
    ss_res_b = np.sum((y_b - y_pred_b) ** 2)
    ss_tot_b = np.sum((y_b - y_b.mean()) ** 2)
    r2_b = 1 - ss_res_b / ss_tot_b if ss_tot_b > 0 else 0
    batch_hp_results[batch] = {
        'n': n_b, 'H0': beta_b[0], 'kH': beta_b[1], 'R2': r2_b,
        'd_inv_sqrt': d_b, 'y': y_b, 'beta': beta_b,
    }
    print(f"  Batch {batch}: n={n_b}, H₀={beta_b[0]:.1f}, k_H={beta_b[1]:.1f}, R²={r2_b:.3f}")

# ---- FIGURE 52: HV scaling laws 2×2 ----
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# (a) HV vs d^(-1/2) with batch colors
ax = axes[0, 0]
for batch in sorted(set(groups)):
    mask = groups == batch
    ax.scatter(d_inv_sqrt[mask], y[mask], c=BATCH_COLORS.get(batch, 'gray'),
               label=batch, s=40, alpha=0.7, edgecolors='k', linewidths=0.3)
x_fit = np.linspace(d_inv_sqrt.min(), d_inv_sqrt.max(), 100)
ax.plot(x_fit, H0_global + kH_global * x_fit, 'k-', linewidth=2)
ax.set_xlabel('d⁻¹/² (µm⁻¹/²)')
ax.set_ylabel('HV (kgf/mm²)')
ax.set_title(f'(a) HV Hall–Petch: H₀={H0_global:.1f}, k_H={kH_global:.0f}, R²={hp_res["r2_train"]:.3f}')
ax.legend(fontsize=8, ncol=2)

# (b) ΔBIC bar chart
ax = axes[0, 1]
colors = ['#2ECC71' if db < 2 else '#F39C12' if db < 6 else '#E74C3C' for db in scale_df['ΔBIC']]
bars = ax.barh(range(len(scale_df)), scale_df['ΔBIC'].values, color=colors,
               edgecolor='k', linewidth=0.5)
ax.set_yticks(range(len(scale_df)))
ax.set_yticklabels([s.split('[')[0].strip() for s in scale_df['Scaling'].values], fontsize=9)
ax.set_xlabel('ΔBIC')
ax.set_title('(b) Scaling Law Comparison (ΔBIC)')
ax.axvline(x=2, color='gray', linestyle='--', linewidth=0.8, label='ΔBIC = 2')
ax.axvline(x=6, color='gray', linestyle=':', linewidth=0.8, label='ΔBIC = 6')
ax.legend(fontsize=8)
ax.invert_yaxis()

# (c) R² vs exponent (HV + YS overlay)
ax = axes[1, 0]
ax.plot(exponents, r2_vs_exp_hv, 'b-', linewidth=2, label='HV')
ax.plot(exponents, r2_vs_exp_ys, 'r--', linewidth=2, label='YS')
ax.axvline(x=n_opt_hv, color='blue', linestyle=':', linewidth=1, label=f'n_opt(HV)={n_opt_hv:.3f}')
ax.axvline(x=n_opt_ys, color='red', linestyle=':', linewidth=1, label=f'n_opt(YS)={n_opt_ys:.3f}')
ax.axvline(x=0.5, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='n=0.5 (HP)')
ax.set_xlabel('Exponent n in d⁻ⁿ')
ax.set_ylabel('Train R²')
ax.set_title('(c) R² vs Exponent: HV and YS')
ax.legend(fontsize=8)

# (d) Per-batch HP fits
ax = axes[1, 1]
for batch, res in batch_hp_results.items():
    color = BATCH_COLORS.get(batch, 'gray')
    ax.scatter(res['d_inv_sqrt'], res['y'], c=color, s=30, alpha=0.6,
               edgecolors='k', linewidths=0.2)
    x_fit = np.linspace(res['d_inv_sqrt'].min(), res['d_inv_sqrt'].max(), 50)
    ax.plot(x_fit, res['beta'][0] + res['beta'][1] * x_fit, color=color,
            linewidth=1.5, label=f"{batch} (k_H={res['kH']:.0f})")
ax.set_xlabel('d⁻¹/² (µm⁻¹/²)')
ax.set_ylabel('HV (kgf/mm²)')
ax.set_title('(d) Per-Batch HP Fits for HV')
ax.legend(fontsize=7, ncol=2)

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/52_HV_scaling_laws.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 52_HV_scaling_laws.png")


# ============================================================
# SECTION C: COMPOSITION-DEPENDENT H₀ MODELS  (Figures 53–54)
# ============================================================
print("\n" + "=" * 70)
print("SECTION C: COMPOSITION-DEPENDENT H₀ MODELS FOR HV")
print("=" * 70)

# Model hierarchy (parallel to composition_hp_analysis.py for YS)
models_spec = {
    'M0: Baseline HP': {
        'X': np.column_stack([ones, d_inv_sqrt]),
        'labels': ['H₀', 'k_H'],
        'group': 'A: H₀ only',
        'desc': 'H₀ + k_H·d⁻¹/²',
    },
    'M1: H₀(V)': {
        'X': np.column_stack([ones, V_hv, d_inv_sqrt]),
        'labels': ['H₀₀', 'α_V', 'k_H'],
        'group': 'A: H₀ only',
        'desc': '(H₀₀ + α_V·V) + k_H·d⁻¹/²',
    },
    'M3: H₀(all elem)': {
        'X': np.column_stack([ones, X_elem_hv, d_inv_sqrt]),
        'labels': ['H₀₀'] + [f'α_{e}' for e in elem_short] + ['k_H'],
        'group': 'A: H₀ only',
        'desc': '(H₀₀ + Σα_i·x_i) + k_H·d⁻¹/²',
    },
    'M4: k_H(V)': {
        'X': np.column_stack([ones, d_inv_sqrt, V_hv * d_inv_sqrt]),
        'labels': ['H₀', 'k₀', 'β_V'],
        'group': 'B: k_H only',
        'desc': 'H₀ + (k₀ + β_V·V)·d⁻¹/²',
    },
    'M6: k_H(all elem)': {
        'X': np.column_stack([ones, d_inv_sqrt] + [X_elem_hv[:, i] * d_inv_sqrt for i in range(7)]),
        'labels': ['H₀', 'k₀'] + [f'β_{e}' for e in elem_short],
        'group': 'B: k_H only',
        'desc': 'H₀ + (k₀ + Σβ_i·x_i)·d⁻¹/²',
    },
    'M10: H₀(all)+k_H(all)': {
        'X': np.column_stack([ones, X_elem_hv, d_inv_sqrt] + [X_elem_hv[:, i] * d_inv_sqrt for i in range(7)]),
        'labels': ['H₀₀'] + [f'α_{e}' for e in elem_short] + ['k₀'] + [f'β_{e}' for e in elem_short],
        'group': 'C: Both',
        'desc': '(H₀₀+Σα·x) + (k₀+Σβ·x)·d⁻¹/²',
    },
}

ols_results = {}
print(f"\n  {'Model':<28s} {'k':>3s} {'Train R²':>9s} {'LOO R²':>8s} {'RMSE':>6s} {'BIC':>8s} {'ΔBIC':>6s}")
print("  " + "-" * 75)

for name, spec in models_spec.items():
    X = spec['X']
    res = ols_loo(X, y)
    ols_results[name] = res

bic_min = min(r['bic'] for r in ols_results.values())
for name in models_spec:
    r = ols_results[name]
    dbic = r['bic'] - bic_min
    print(f"  {name:<28s} {r['k_params']:>3d} {r['r2_train']:>9.4f} {r['r2_loo']:>8.4f} "
          f"{r['loo_rmse']:>6.1f} {r['bic']:>8.1f} {dbic:>6.1f}")

# Save model comparison
model_rows = []
for name, spec in models_spec.items():
    r = ols_results[name]
    model_rows.append({
        'Model': name, 'Group': spec['group'], 'Desc': spec['desc'],
        'k': r['k_params'], 'Train_R2': r['r2_train'],
        'LOO_R2': r['r2_loo'], 'LOO_RMSE': r['loo_rmse'],
        'AIC': r['aic'], 'BIC': r['bic'],
    })
model_df = pd.DataFrame(model_rows)
model_df['ΔBIC'] = model_df['BIC'] - model_df['BIC'].min()
model_df.to_csv(f'{RESULTS_DIR}/hardness_model_comparison.csv', index=False)
print(f"\n  Saved hardness_model_comparison.csv")

# Best model
best_name = model_df.loc[model_df['LOO_R2'].idxmax(), 'Model']
best_res = ols_results[best_name]
print(f"\n  Best by LOO R²: {best_name} (R² = {best_res['r2_loo']:.4f})")

# Extract M3 coefficients for comparison with YS
m3_res = ols_results['M3: H₀(all elem)']
m3_beta = m3_res['beta']
m3_labels = models_spec['M3: H₀(all elem)']['labels']
print(f"\n  M3 Coefficients (HV):")
for lbl, b in zip(m3_labels, m3_beta):
    print(f"    {lbl:>6s} = {b:>8.1f}")

# Two-stage k_H analysis (parallel to kHP_composition_analysis.py)
print("\n  Two-stage k_H composition analysis:")
H0_comp = np.column_stack([ones, X_elem_hv]) @ m3_beta[:8]  # H₀(comp) per alloy
kH_eff = (y - H0_comp) / d_inv_sqrt  # effective k_H per alloy
print(f"    k_H_eff range: {kH_eff.min():.0f}–{kH_eff.max():.0f} HV·µm¹/²")
print(f"    k_H_eff mean:  {kH_eff.mean():.0f} ± {kH_eff.std():.0f}")

# Regress k_H_eff on composition
X_k = np.column_stack([ones, X_elem_hv])
beta_k = np.linalg.lstsq(X_k, kH_eff, rcond=None)[0]
kH_pred = X_k @ beta_k
ss_res_k = np.sum((kH_eff - kH_pred) ** 2)
ss_tot_k = np.sum((kH_eff - kH_eff.mean()) ** 2)
r2_kH = 1 - ss_res_k / ss_tot_k
f_stat_k = (r2_kH / 7) / ((1 - r2_kH) / (n - 8))
p_f_k = stats.f.sf(f_stat_k, 7, n - 8)
print(f"    R²(k_H_eff ~ composition) = {r2_kH:.4f}, F-test p = {p_f_k:.4f}")

# Also fit YS M3 for coefficient comparison
d_inv_sqrt_ys = d_ys ** -0.5
X_elem_ys = df_ys[elem_names].values.astype(float)
X_m3_ys = np.column_stack([np.ones(n_ys), X_elem_ys, d_inv_sqrt_ys])
beta_m3_ys = np.linalg.lstsq(X_m3_ys, y_ys, rcond=None)[0]

print(f"\n  M3 Coefficient Comparison (HV vs YS):")
print(f"  {'Param':>8s} {'HV':>10s} {'YS':>10s} {'Ratio':>8s}")
print("  " + "-" * 40)
for j, lbl in enumerate(m3_labels):
    ratio = m3_beta[j] / beta_m3_ys[j] if abs(beta_m3_ys[j]) > 1e-6 else np.nan
    print(f"  {lbl:>8s} {m3_beta[j]:>10.1f} {beta_m3_ys[j]:>10.1f} {ratio:>8.2f}")

# ---- FIGURE 53: Composition HV models 1×3 ----
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# (a) LOO R² bar chart
ax = axes[0]
names_short = [n.split(':')[0] for n in models_spec.keys()]
loo_r2s = [ols_results[n]['r2_loo'] for n in models_spec.keys()]
group_colors = {'A: H₀ only': '#3498DB', 'B: k_H only': '#E74C3C', 'C: Both': '#2ECC71'}
colors = [group_colors.get(models_spec[n]['group'], 'gray') for n in models_spec.keys()]
ax.barh(range(len(names_short)), loo_r2s, color=colors, edgecolor='k', linewidth=0.5)
ax.set_yticks(range(len(names_short)))
ax.set_yticklabels(names_short)
ax.set_xlabel('LOO R²')
ax.set_title('(a) LOO R² by Model')
ax.invert_yaxis()

# (b) ΔBIC bar chart
ax = axes[1]
dbics = [ols_results[n]['bic'] - bic_min for n in models_spec.keys()]
ax.barh(range(len(names_short)), dbics, color=colors, edgecolor='k', linewidth=0.5)
ax.set_yticks(range(len(names_short)))
ax.set_yticklabels(names_short)
ax.set_xlabel('ΔBIC')
ax.set_title('(b) ΔBIC by Model')
ax.axvline(x=2, color='gray', linestyle='--', linewidth=0.8)
ax.invert_yaxis()

# (c) LOO parity plot for best model
ax = axes[2]
best_loo = best_res['loo_pred']
ax.scatter(y, best_loo, c='steelblue', s=40, alpha=0.7, edgecolors='k', linewidths=0.3)
lims = [min(y.min(), best_loo.min()) - 5, max(y.max(), best_loo.max()) + 5]
ax.plot(lims, lims, 'k--', linewidth=1)
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_xlabel('Observed HV')
ax.set_ylabel('LOO Predicted HV')
ax.set_title(f'(c) Parity: {best_name} (LOO R²={best_res["r2_loo"]:.3f})')
ax.set_aspect('equal')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/53_comp_HV_models.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 53_comp_HV_models.png")

# ---- FIGURE 54: HV vs YS coefficients 1×3 ----
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# (a) M3 α_i coefficients for HV (bar chart)
ax = axes[0]
alpha_hv = m3_beta[1:8]  # 7 element coefficients
ax.bar(range(7), alpha_hv, color='steelblue', edgecolor='k', linewidth=0.5)
ax.set_xticks(range(7))
ax.set_xticklabels(elem_short)
ax.set_ylabel('α_i (HV units)')
ax.set_title('(a) M3 Element Coefficients (HV)')
ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

# (b) α_i(HV) vs α_i(YS) scatter with Tabor line
ax = axes[1]
alpha_ys = beta_m3_ys[1:8]
ax.scatter(alpha_ys, alpha_hv, c='steelblue', s=80, edgecolors='k', linewidths=0.5, zorder=5)
for j, e in enumerate(elem_short):
    ax.annotate(e, (alpha_ys[j], alpha_hv[j]), textcoords="offset points",
                xytext=(5, 5), fontsize=9)
# Tabor scaling line: α_i(HV) = (C_eff_mean / 9.807) × α_i(YS)
tabor_scale = C_eff.mean() / 9.807
ys_range = np.array([alpha_ys.min() - 50, alpha_ys.max() + 50])
ax.plot(ys_range, tabor_scale * ys_range, 'r--', linewidth=1.5,
        label=f'Tabor scaling (×{tabor_scale:.3f})')
# Best fit line
slope_ab, intercept_ab, r_ab, _, _ = stats.linregress(alpha_ys, alpha_hv)
ax.plot(ys_range, intercept_ab + slope_ab * ys_range, 'b-', linewidth=1.5,
        label=f'Best fit (slope={slope_ab:.3f}, r={r_ab:.3f})')
ax.set_xlabel('α_i (YS, MPa)')
ax.set_ylabel('α_i (HV)')
ax.set_title('(b) Coefficient Comparison: HV vs YS')
ax.legend(fontsize=8)

# (c) k_H_eff vs composition: per-element r, p summary
ax = axes[2]
elem_r_kH = []
for i, elem in enumerate(elem_short):
    r, p = stats.pearsonr(X_elem_hv[:, i], kH_eff)
    elem_r_kH.append(r)
colors_kH = ['#E74C3C' if abs(r) > 0.2 else '#3498DB' for r in elem_r_kH]
ax.bar(range(7), elem_r_kH, color=colors_kH, edgecolor='k', linewidth=0.5)
ax.set_xticks(range(7))
ax.set_xticklabels(elem_short)
ax.set_ylabel('Pearson r (k_H_eff vs x_i)')
ax.set_title(f'(c) k_H Composition Dependence (R²={r2_kH:.4f})')
ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/54_HV_YS_coefficients.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 54_HV_YS_coefficients.png")


# ============================================================
# SECTION D: JOINT HV–YS ANALYSIS  (Figure 55)
# ============================================================
print("\n" + "=" * 70)
print("SECTION D: JOINT HV–YS ANALYSIS & LITERATURE CONTEXT")
print("=" * 70)

# H₀ vs σ₀ per alloy (from M3 fits)
H0_alloy = np.column_stack([np.ones(n_hv), X_elem_hv]) @ m3_beta[:8]

# For YS M3: σ₀ per alloy (need alloys with both)
# Use df_both which has both HV and YS
X_elem_b = df_both[elem_names].values.astype(float)
sigma0_alloy = np.column_stack([np.ones(n_both), X_elem_b]) @ beta_m3_ys[:8]
# H0 for the same alloys
H0_alloy_both = np.column_stack([np.ones(n_both), X_elem_b]) @ m3_beta[:8]

r_H0_sig0, p_H0_sig0 = stats.pearsonr(sigma0_alloy, H0_alloy_both)
print(f"\n  H₀ vs σ₀ correlation: r = {r_H0_sig0:.3f}, p = {p_H0_sig0:.6f}")

# k_H vs k_HP comparison
kHP_ys = beta_m3_ys[-1]  # global k_HP from YS M3
kH_hv = m3_beta[-1]      # global k_H from HV M3
kH_MPa = kH_hv * 9.807
print(f"  k_HP (YS) = {kHP_ys:.0f} MPa·µm¹/²")
print(f"  k_H  (HV) = {kH_hv:.1f} HV·µm¹/²  = {kH_MPa:.0f} MPa·µm¹/²")
print(f"  k_H(MPa) / k_HP = {kH_MPa / kHP_ys:.2f}")
print(f"  Expected (C_eff) = {C_eff.mean():.2f}")

# Residuals after HP removal
resid_hv = hv_both - (H0_global + kH_global * d_inv_sqrt_both)
hp_ys_res = ols_loo(np.column_stack([np.ones(n_both), d_inv_sqrt_both]), ys_both)
resid_ys = ys_both - hp_ys_res['y_pred']
r_resid, p_resid = stats.pearsonr(resid_ys, resid_hv)
print(f"\n  Residual correlation (after HP): r = {r_resid:.3f}, p = {p_resid:.6f}")

# Literature k_H values (Sathiyamoorthi & Kim 2019, Entropy)
lit_kH = {
    'CoCrFeMnNi (Cantor)': 494 / 9.807,
    'CoCrNi': 677 / 9.807,
    'CoCrFeMnNi (Sun 2019)': 526 / 9.807,
    'Fe-20Mn-12Cr': 370 / 9.807,
    'This work (global)': kH_global,
}
# Convert to MPa for literature comparison
lit_kH_MPa = {k: v * 9.807 for k, v in lit_kH.items()}

print(f"\n  Literature k_H comparison (MPa·µm¹/²):")
for name, val in lit_kH_MPa.items():
    print(f"    {name:<30s}: {val:.0f}")

# H₀/σ₀ ratio per alloy
H0_sig0_ratio = H0_alloy_both / sigma0_alloy
print(f"\n  H₀/σ₀ ratio: mean = {H0_sig0_ratio.mean():.3f}, std = {H0_sig0_ratio.std():.3f}")
print(f"  Expected (C_eff/9.807) = {C_eff.mean() / 9.807:.3f}")

# ---- FIGURE 55: Joint analysis 2×2 ----
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# (a) H₀(alloy) vs σ₀(alloy)
ax = axes[0, 0]
ax.scatter(sigma0_alloy, H0_alloy_both, c='steelblue', s=40, alpha=0.7,
           edgecolors='k', linewidths=0.3)
# Tabor line: H₀ = (C_eff_mean / 9.807) × σ₀
sig_range = np.array([sigma0_alloy.min() - 10, sigma0_alloy.max() + 10])
ax.plot(sig_range, tabor_scale * sig_range, 'r--', linewidth=1.5,
        label=f'Tabor (×{tabor_scale:.3f})')
slope_h, intercept_h, r_h, _, _ = stats.linregress(sigma0_alloy, H0_alloy_both)
ax.plot(sig_range, intercept_h + slope_h * sig_range, 'b-', linewidth=1.5,
        label=f'Fit (r={r_h:.3f})')
ax.set_xlabel('σ₀ (MPa) from YS M3')
ax.set_ylabel('H₀ (HV) from HV M3')
ax.set_title(f'(a) H₀ vs σ₀ (r = {r_H0_sig0:.3f})')
ax.legend(fontsize=9)

# (b) Residual HV vs residual YS (after HP removal)
ax = axes[0, 1]
ax.scatter(resid_ys, resid_hv, c='steelblue', s=40, alpha=0.7,
           edgecolors='k', linewidths=0.3)
slope_r, intercept_r, _, _, _ = stats.linregress(resid_ys, resid_hv)
ys_r_range = np.array([resid_ys.min(), resid_ys.max()])
ax.plot(ys_r_range, intercept_r + slope_r * ys_r_range, 'r-', linewidth=1.5)
ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.8)
ax.set_xlabel('YS Residual (MPa)')
ax.set_ylabel('HV Residual')
ax.set_title(f'(b) HP Residuals: HV vs YS (r = {r_resid:.3f})')

# (c) k_H literature comparison bar chart
ax = axes[1, 0]
lit_names = list(lit_kH_MPa.keys())
lit_vals = list(lit_kH_MPa.values())
colors_lit = ['steelblue'] * (len(lit_names) - 1) + ['#E74C3C']
ax.barh(range(len(lit_names)), lit_vals, color=colors_lit, edgecolor='k', linewidth=0.5)
ax.set_yticks(range(len(lit_names)))
ax.set_yticklabels(lit_names, fontsize=9)
ax.set_xlabel('k_H (MPa·µm¹/²)')
ax.set_title('(c) k_H Literature Comparison')
ax.invert_yaxis()

# (d) Effective Tabor: H₀/σ₀ vs k_H/k_HP
ax = axes[1, 1]
ax.scatter(H0_sig0_ratio, np.full(n_both, kH_MPa / kHP_ys),
           c='steelblue', s=40, alpha=0.5, edgecolors='k', linewidths=0.3)
ax.axhline(y=C_eff.mean(), color='red', linestyle='--', linewidth=1.5,
           label=f'C_eff = {C_eff.mean():.2f}')
ax.axvline(x=C_eff.mean() / 9.807, color='orange', linestyle='--', linewidth=1.5,
           label=f'C_eff/g = {C_eff.mean()/9.807:.3f}')
ax.set_xlabel('H₀/σ₀ per alloy')
ax.set_ylabel('k_H(MPa) / k_HP')
ax.set_title('(d) Tabor Factor: Intercept vs Slope')
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/55_HV_YS_joint.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 55_HV_YS_joint.png")


# ============================================================
# SECTION E: RANK CORRELATION ANALYSIS  (Figure 56)
# ============================================================
print("\n" + "=" * 70)
print("SECTION E: RANK CORRELATION — HV vs YS RANKINGS")
print("=" * 70)

# Spearman and Kendall rank correlations (global)
spearman_rho, spearman_p = stats.spearmanr(hv_both, ys_both)
kendall_tau, kendall_p = stats.kendalltau(hv_both, ys_both)
print(f"\n  Global rank correlations:")
print(f"    Spearman ρ = {spearman_rho:.3f} (p = {spearman_p:.2e})")
print(f"    Kendall  τ = {kendall_tau:.3f} (p = {kendall_p:.2e})")

# Compute ranks (1 = highest)
df_both['rank_HV'] = df_both['HV'].rank(ascending=False)
df_both['rank_YS'] = df_both['YS'].rank(ascending=False)
df_both['rank_diff'] = df_both['rank_HV'] - df_both['rank_YS']

# Within-batch Spearman
print(f"\n  Within-batch Spearman ρ:")
batch_spearman = {}
for batch in sorted(set(batches_both)):
    mask = batches_both == batch
    if mask.sum() >= 5:
        rho_b, p_b = stats.spearmanr(hv_both[mask], ys_both[mask])
        batch_spearman[batch] = rho_b
        print(f"    {batch}: ρ = {rho_b:.3f} (n={mask.sum()})")

# Top-10 overlap
top10_hv = set(df_both.nlargest(10, 'HV').index)
top10_ys = set(df_both.nlargest(10, 'YS').index)
overlap_10 = len(top10_hv & top10_ys)
top20_hv = set(df_both.nlargest(20, 'HV').index)
top20_ys = set(df_both.nlargest(20, 'YS').index)
overlap_20 = len(top20_hv & top20_ys)
print(f"\n  Top-10 overlap: {overlap_10}/10 alloys")
print(f"  Top-20 overlap: {overlap_20}/20 alloys")

# Biggest rank mismatches
print(f"\n  Largest rank mismatches (HV rank − YS rank):")
print(f"    Ranked higher in HV than YS:")
for _, row in df_both.nlargest(3, 'rank_diff').iterrows():
    print(f"      {row['Alloy']} ({row['Iteration']}): HV rank={row['rank_HV']:.0f}, "
          f"YS rank={row['rank_YS']:.0f}, Δ={row['rank_diff']:.0f}, d={row['GrainSize']:.0f} µm")
print(f"    Ranked higher in YS than HV:")
for _, row in df_both.nsmallest(3, 'rank_diff').iterrows():
    print(f"      {row['Alloy']} ({row['Iteration']}): HV rank={row['rank_HV']:.0f}, "
          f"YS rank={row['rank_YS']:.0f}, Δ={row['rank_diff']:.0f}, d={row['GrainSize']:.0f} µm")

# ---- FIGURE 56: Rank correlation 2×2 ----
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# (a) Rank HV vs Rank YS, colored by batch
ax = axes[0, 0]
for batch in sorted(set(batches_both)):
    mask = batches_both == batch
    ax.scatter(df_both.loc[df_both['Iteration'] == batch, 'rank_YS'],
               df_both.loc[df_both['Iteration'] == batch, 'rank_HV'],
               c=BATCH_COLORS.get(batch, 'gray'), label=batch,
               s=40, alpha=0.7, edgecolors='k', linewidths=0.3)
lims = [0, n_both + 1]
ax.plot(lims, lims, 'k--', linewidth=1, alpha=0.5)
ax.set_xlabel('YS Rank (1 = strongest)')
ax.set_ylabel('HV Rank (1 = hardest)')
ax.set_title(f'(a) Rank Comparison (Spearman ρ = {spearman_rho:.3f})')
ax.legend(fontsize=8, ncol=2)
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.invert_xaxis()
ax.invert_yaxis()

# (b) Within-batch vs global Spearman rho
ax = axes[0, 1]
batch_names = list(batch_spearman.keys())
batch_rhos = list(batch_spearman.values())
colors_rho = [BATCH_COLORS.get(b, 'gray') for b in batch_names]
bars = ax.bar(range(len(batch_names)), batch_rhos, color=colors_rho,
              edgecolor='k', linewidth=0.5)
ax.bar(len(batch_names), spearman_rho, color='#555555', edgecolor='k', linewidth=0.5)
ax.set_xticks(range(len(batch_names) + 1))
ax.set_xticklabels(batch_names + ['Global'], fontsize=9)
ax.set_ylabel('Spearman ρ')
ax.set_title('(b) Within-Batch vs Global Rank Correlation')
ax.axhline(y=0.7, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)
ax.set_ylim(0, 1.05)
# Annotate values
for i, v in enumerate(batch_rhos + [spearman_rho]):
    ax.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=8)

# (c) Rank difference vs grain size — shows batch-driven mismatches
ax = axes[1, 0]
for batch in sorted(set(batches_both)):
    mask_b = df_both['Iteration'] == batch
    ax.scatter(df_both.loc[mask_b, 'GrainSize'],
               df_both.loc[mask_b, 'rank_diff'],
               c=BATCH_COLORS.get(batch, 'gray'), label=batch,
               s=40, alpha=0.7, edgecolors='k', linewidths=0.3)
ax.axhline(y=0, color='k', linestyle='-', linewidth=0.8)
ax.set_xlabel('Grain Size (µm)')
ax.set_ylabel('Rank Difference (HV rank − YS rank)')
ax.set_title('(c) Rank Mismatch vs Grain Size')
ax.legend(fontsize=8, ncol=2)
# Add annotation for interpretation
ax.text(0.03, 0.97, 'Positive = ranked\nhigher in HV', transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic', color='gray')
ax.text(0.03, 0.03, 'Negative = ranked\nhigher in YS', transform=ax.transAxes,
        fontsize=8, va='bottom', ha='left', style='italic', color='gray')

# (d) Top-10 highlight: HV vs YS with top-10 marked
ax = axes[1, 1]
ax.scatter(ys_both, hv_both, c='lightgray', s=30, edgecolors='gray', linewidths=0.3,
           zorder=1, label='All alloys')
# Top 10 by YS
top10_ys_mask = df_both.index.isin(top10_ys)
ax.scatter(df_both.loc[top10_ys_mask, 'YS'], df_both.loc[top10_ys_mask, 'HV'],
           c='#E74C3C', s=70, edgecolors='k', linewidths=0.5, marker='s',
           zorder=3, label='Top 10 by YS')
# Top 10 by HV
top10_hv_mask = df_both.index.isin(top10_hv)
ax.scatter(df_both.loc[top10_hv_mask, 'YS'], df_both.loc[top10_hv_mask, 'HV'],
           c='#3498DB', s=70, edgecolors='k', linewidths=0.5, marker='^',
           zorder=3, label='Top 10 by HV')
# Overlap (both)
overlap_mask = df_both.index.isin(top10_hv & top10_ys)
ax.scatter(df_both.loc[overlap_mask, 'YS'], df_both.loc[overlap_mask, 'HV'],
           c='#2ECC71', s=90, edgecolors='k', linewidths=0.8, marker='D',
           zorder=4, label=f'Both top 10 ({overlap_10}/10)')
ax.set_xlabel('Yield Strength (MPa)')
ax.set_ylabel('HV (kgf/mm²)')
ax.set_title(f'(d) Top-10 Overlap: {overlap_10}/10 shared')
ax.legend(fontsize=8, loc='lower right')

plt.tight_layout()
plt.savefig(f'{PLOT_DIR}/56_rank_correlation.png', dpi=200, bbox_inches='tight')
plt.close()
print(f"\n  Saved 56_rank_correlation.png")

# Clean up temporary columns
df_both.drop(columns=['rank_HV', 'rank_YS', 'rank_diff'], inplace=True)


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"\n  Tabor Relation:")
print(f"    C_eff = {C_eff.mean():.2f} ± {C_eff.std():.2f} (classical = 3.0)")
print(f"    Significantly {'different from' if p_val < 0.05 else 'not different from'} 3 (p = {p_val:.4f})")
print(f"    Composition R² = {r2_c:.3f}")
print(f"    Inferred UTS/YS = {UTS_YS_ratio.mean():.2f}")

print(f"\n  HV Hall–Petch:")
print(f"    H₀ = {H0_global:.1f} HV, k_H = {kH_global:.1f} HV·µm¹/²")
print(f"    k_H = {kH_MPa:.0f} MPa·µm¹/²")
print(f"    Train R² = {hp_res['r2_train']:.4f}, LOO R² = {hp_res['r2_loo']:.4f}")
print(f"    Optimal exponent: {n_opt_hv:.3f} (YS: {n_opt_ys:.3f})")

print(f"\n  Composition Models:")
print(f"    Best by LOO R²: {best_name} (R² = {best_res['r2_loo']:.4f})")
print(f"    k_H composition dependence: R² = {r2_kH:.4f} (negligible)")

print(f"\n  Joint Analysis:")
print(f"    H₀–σ₀ correlation: r = {r_H0_sig0:.3f}")
print(f"    k_H(MPa)/k_HP = {kH_MPa / kHP_ys:.2f} (vs C_eff = {C_eff.mean():.2f})")
print(f"    Residual correlation: r = {r_resid:.3f}")

print(f"\n  Rank Correlation:")
print(f"    Spearman ρ (global) = {spearman_rho:.3f}")
print(f"    Within-batch ρ range: {min(batch_spearman.values()):.3f}–{max(batch_spearman.values()):.3f}")
print(f"    Top-10 overlap: {overlap_10}/10, Top-20 overlap: {overlap_20}/20")
print(f"    Simpson's paradox: batch confounding suppresses global correlation")

print(f"\n  Figures saved: 50–56 in {PLOT_DIR}/")
print(f"  CSVs saved: hardness_scaling_comparison.csv, hardness_model_comparison.csv")
print("\n" + "=" * 70)
print("HARDNESS ANALYSIS COMPLETE")
print("=" * 70)
