#!/usr/bin/env python3
"""
Corrected VLC Solid Solution Strengthening Model
=================================================
Fixes the Delta_Eb formula bug and recomputes SSS for all alloys.

Correct VLC formulas (Varvenne & Curtin, Scripta Mater. 142, 2017):
  tau_y0  = 0.051 * alpha^(-1/3) * f1^(2/3)   * mu * Q^(2/3)
  Delta_Eb = 0.274 * alpha^(1/3) * f1^(1/3)   * mu * b^3 * Q^(1/3)

  where Q = sum_n c_n * (dV_n/V_bar)^2   (dimensionless misfit variance)
        f1 = ((1+nu)/(1-nu))^2 * 4/9
        alpha = 0.123

  Finite-T:  tau_y(T) = tau_y0 * [1 - (kT/Delta_Eb)^(2/3)]
  Polycryst: sigma_y = M * tau_y(T),  M = 3.06
"""

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/ (for _config)
from _config import REPO_ROOT, DATA_DIR, RAW_DATA_DIR, RESULTS_DIR, PLOTS_DIR, PAPER_DIR, PAPER_FIG_DIR
BASE = str(REPO_ROOT)
ELEMENTS = ['Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'Ni', 'V']

# ============================================================
# ELEMENT PHYSICAL PROPERTIES
# ============================================================
# FCC lattice parameters (Angstrom) — for Vegard's law on the alloy lattice constant.
A_FCC = {'Al': 4.050, 'Co': 3.545, 'Cr': 3.520, 'Cu': 3.615,
         'Fe': 3.590, 'Mn': 3.540, 'Ni': 3.524, 'V': 3.720}  # Fe: 3.590 Å (gamma-Fe FCC)
ATOMIC_VOL = {el: (a * 1e-10)**3 / 4 for el, a in A_FCC.items()}  # m^3 (pure-element FCC volume)

# Atomic volumes used by Varvenne 2016 (Acta Mater 118:164) for the VLC theory.
# For Ni-Co-Fe-Cr-Mn, V_n derived from measured Ni-X binary FCC solid solutions
# (Varvenne 2016 Table 1 + text on p7).  For Al, Cu, V — outside the Varvenne
# benchmark family — we fall back on pure-element FCC volumes (extrapolated for
# V, which is BCC in pure form, and for Mn, which is alpha-Mn).
V_VARVENNE_A3 = {  # Å^3, per atom
    'Ni': 10.94, 'Co': 11.12, 'Fe': 12.09, 'Cr': 12.27, 'Mn': 12.60,
    'Al': ATOMIC_VOL['Al'] * 1e30,
    'Cu': ATOMIC_VOL['Cu'] * 1e30,
    'V':  ATOMIC_VOL['V']  * 1e30,
}

# Metallic radii (pm) — Goldschmidt
RADII = {'Al': 143, 'Co': 125, 'Cr': 128, 'Cu': 128, 'Fe': 126, 'Mn': 127, 'Ni': 124, 'V': 134}

# Shear modulus (GPa)
SHEAR_MOD = {'Al': 26, 'Co': 75, 'Cr': 115, 'Cu': 48, 'Fe': 82, 'Mn': 79, 'Ni': 76, 'V': 47}  # Co: 75 GPa (polycrystalline FCC)

# Bulk modulus (GPa)
BULK_MOD = {'Al': 76, 'Co': 180, 'Cr': 160, 'Cu': 140, 'Fe': 170, 'Mn': 120, 'Ni': 180, 'V': 158}

# Poisson's ratio = (3K - 2G) / (2(3K + G))
POISSON = {el: (3*BULK_MOD[el] - 2*SHEAR_MOD[el]) / (2*(3*BULK_MOD[el] + SHEAR_MOD[el]))
           for el in ELEMENTS}


def compute_vlc_corrected(row, T=300):
    """Faithful Varvenne 2016 VLC SSS computation (Acta Mater 118:164–176, Eqs. 15–16).

    May 2026 rewrite — previous simplified form (incorrect Poisson factor and
    missing f1, f2 core coefficients) replaced with the published equations:

      τ_y0  = 0.051 α^(-1/3) μ [(1+ν)/(1-ν)]^(4/3) f1(w_c) [Σ c_n ΔV_n² / b^6]^(2/3)
      ΔE_b  = 0.274 α^(1/3)  μ b³ [(1+ν)/(1-ν)]^(2/3) f2(w_c) [Σ c_n ΔV_n² / b^6]^(1/3)
      σ_y(T) = M · τ_y0 · [1 − (k_B T / ΔE_b)^(2/3)]

    Numerical constants from Varvenne 2016: α = 0.123 (line tension),
    f1(w_c) = 0.35, f2(w_c) = 5.70 for FCC HEAs at typical γ_SF (their Fig 6),
    M = 3.06 (Taylor factor for random FCC).  Atomic volumes V_n are from
    binary Ni-X solid-solution measurements for Ni-Co-Fe-Cr-Mn (V_VARVENNE_A3),
    falling back to pure-element FCC volumes for Al, Cu, V.
    """
    fracs = {el: row[f'{el}_frac'] for el in ELEMENTS}
    active = {el: c for el, c in fracs.items() if c > 0}

    # Rule-of-mixtures averages (elastic constants)
    mu_bar_Pa = sum(c * SHEAR_MOD[el] * 1e9 for el, c in fracs.items())
    mu_bar_GPa = mu_bar_Pa / 1e9
    nu_bar = sum(c * POISSON[el] for el, c in fracs.items())
    r_bar_pm = sum(c * RADII[el] for el, c in fracs.items())

    # Vegard-law alloy lattice parameter (used by Toda-Caraballo for ds/dX_i)
    a_bar_Vegard_m = sum(c * A_FCC[el] for el, c in fracs.items()) * 1e-10

    # Atomic volume and Burgers vector for VLC — Varvenne uses solution-derived V_n
    # and computes b from V̄ as b = (4V̄)^(1/3)/√2.
    V_bar_A3 = sum(c * V_VARVENNE_A3[el] for el, c in fracs.items())   # Å^3
    V_bar = V_bar_A3 * 1e-30                                            # m^3
    a_bar_A = (4 * V_bar_A3) ** (1.0/3.0)                               # Å (Varvenne convention)
    a_bar_m = a_bar_A * 1e-10
    b_m = a_bar_m / np.sqrt(2)
    b_A = a_bar_A / np.sqrt(2)

    # VLC parameters (Varvenne 2016)
    alpha = 0.123
    f1_VLC = 0.35    # minimized core coefficient for τ_y0 (FCC HEA, Fig 6)
    f2_VLC = 5.70    # minimized core coefficient for ΔE_b
    M_taylor = 3.06
    kB = 1.381e-23  # J/K

    # Poisson factors (exponents 4/3 and 2/3 — Varvenne 2016 Eqs. 15, 16)
    nu_ratio = (1 + nu_bar) / (1 - nu_bar)
    poisson_15 = nu_ratio ** (4.0/3.0)
    poisson_16 = nu_ratio ** (2.0/3.0)

    # Dimensionless misfit quantity Q = Σ c_n ΔV_n² / b^6  (ΔV_n in Å^3, b in Å)
    deltaV_A3 = {el: V_VARVENNE_A3[el] - V_bar_A3 for el in ELEMENTS}
    sum_cdV2 = sum(c * deltaV_A3[el]**2 for el, c in fracs.items())  # Å^6
    Q = sum_cdV2 / (b_A ** 6)                                         # dimensionless

    # τ_y0 (Varvenne 2016 Eq. 15)
    tau_y0 = 0.051 * alpha**(-1.0/3.0) * mu_bar_Pa * poisson_15 * f1_VLC * Q**(2.0/3.0)
    sigma_y0 = M_taylor * tau_y0 / 1e6  # MPa

    # ΔE_b (Varvenne 2016 Eq. 16)
    Delta_Eb = 0.274 * alpha**(1.0/3.0) * mu_bar_Pa * b_m**3 * poisson_16 * f2_VLC * Q**(1.0/3.0)
    Delta_Eb_eV = Delta_Eb / 1.602e-19

    # Finite-temperature correction
    if Delta_Eb > 0 and T > 0:
        ratio = kB * T / Delta_Eb
        if ratio < 1.0:
            T_corr = (1 - ratio**(2.0/3.0))
        else:
            T_corr = 0.0
    else:
        T_corr = 1.0

    sigma_y_T = sigma_y0 * T_corr

    # --- Labusch HEA extension (corrected exponent c_eff^(2/3) per Labusch 1970,
    #     calibrated to Cantor σ_0 = 125 MPa via a one-alloy fit) ---
    # The dilute-alloy Labusch formula τ ∝ μ·ε^(4/3)·c^(2/3) is missing the
    # numerical prefactor 1/Z (Z ∈ [60, 180] from Labusch 1970) and the Taylor
    # factor M. We absorb both into a single calibration constant K_Lab fit so
    # that σ_Labusch(CoCrFeMnNi) = 125 MPa (Otto 2013).  K_Lab = 0.027 implies
    # an effective Z_Lab = M/K_Lab = 1/113, which falls within Labusch's
    # original literature range [60, 180].  Calibration is applied once and
    # held constant throughout the analysis.
    K_LAB_CANTOR = 0.0270  # σ_0,Cantor=125 MPa / σ_Lab,uncal,Cantor=4629 MPa
    delta_r = {el: (RADII[el] - r_bar_pm) / r_bar_pm for el in ELEMENTS}
    delta_mu = {el: (SHEAR_MOD[el] - mu_bar_GPa) / mu_bar_GPa for el in ELEMENTS}
    alpha_L = 16
    eps_sq = sum(c * (delta_mu[el]**2 + alpha_L**2 * delta_r[el]**2) for el, c in fracs.items())
    eps_Labusch = np.sqrt(eps_sq)
    n_comp = len(active)
    c_eff = 1.0 / n_comp
    sigma_Labusch_uncal = mu_bar_GPa * 1000 * eps_Labusch**(4.0/3.0) * c_eff**(2.0/3.0)
    sigma_Labusch = K_LAB_CANTOR * sigma_Labusch_uncal

    # --- Toda-Caraballo 2015 (Acta Mater 85:14-23) — faithful implementation ---
    # NOTE (May 2026): previously used a Yang-δ simplified form. The full TC
    # uses Eqs. 3, 5, 14, 26 with Gypen-Deruyttere superposition:
    #   B_i = 3 μ̄ ε_i^(4/3) Z;   ε_i = sqrt(η'_i^2 + α^2 δ_i^2);   α = 16 (FCC edge)
    #   η_i = 2(μ_i - μ̄)/(μ_i + μ̄);   η'_i = η_i / (1 + 0.5|η_i|)         (Eqs. 3, 26)
    #   δ_i = (a_i - ā)/ā                                          (Vegard approx of ds/dX_i)
    #   Δτ_rss = (Σ_i B_i^(3/2) · X_i)^(2/3)                                (Eq. 14)
    #   σ_y    = M · Δτ_rss                                                  (M = 3.06)
    # Z = 1/180 follows from Labusch's original derivation (no fitting).
    # Toda-Caraballo 2015 Z calibrated to Cantor (σ_TC,uncal=446 MPa with Z=1/180;
    # Cantor σ_0=125 MPa → Z_calibrated = 1/642).  This absorbs the empirical
    # B_i fitting that Toda-Caraballo's own paper performs against binary alloy
    # data (their Fig. 4) into a single one-alloy calibration, then holds Z
    # constant throughout the analysis.  The calibrated value Z = 1/642 is
    # outside Labusch's standard range [60, 180], reflecting that TC's
    # Gypen-Deruyttere superposition absorbs additional unmodeled physics.
    alpha_TC = 16.0
    Z_TC = 1.0 / 642.0  # calibrated to CoCrFeMnNi σ_0 = 125 MPa (Otto 2013)
    a_bar_Vegard_A = a_bar_Vegard_m * 1e10
    sumB_pow = 0.0
    for el, c in active.items():
        eta_i  = 2 * (SHEAR_MOD[el] - mu_bar_GPa) / (SHEAR_MOD[el] + mu_bar_GPa)  # Eq. 26
        etap_i = eta_i / (1.0 + 0.5 * abs(eta_i))                                  # Eq. 3
        delta_i = (A_FCC[el] - a_bar_Vegard_A) / a_bar_Vegard_A                    # ds/dX_i (Vegard)
        eps_i = np.sqrt(etap_i**2 + (alpha_TC * delta_i)**2)                       # Eq. 5/13 (FCC: n=1)
        B_i = 3.0 * (mu_bar_Pa) * (eps_i**(4.0/3.0)) * Z_TC                        # Pa
        sumB_pow += (B_i ** 1.5) * c
    Drss_TC = sumB_pow ** (2.0 / 3.0)                                              # Pa
    sigma_TC = M_taylor * Drss_TC / 1e6                                            # MPa
    # Also keep Yang's δ for use as a descriptor (Φ-style, not as a model)
    delta_Yang = np.sqrt(sum(c * delta_r[el]**2 for el, c in fracs.items()))

    return pd.Series({
        'mu_bar_GPa': mu_bar_GPa,
        'nu_bar': nu_bar,
        'a_bar_A': a_bar_m * 1e10,
        'b_A': b_m * 1e10,
        'Q_misfit': Q,
        'tau_y0_MPa': tau_y0 / 1e6,
        'sigma_y0_VLC': sigma_y0,
        'Delta_Eb_eV': Delta_Eb_eV,
        'kT_over_Eb': kB * T / Delta_Eb if Delta_Eb > 0 else np.inf,
        'T_correction': T_corr,
        'sigma_y_VLC_300K': sigma_y_T,
        'sigma_Labusch': sigma_Labusch,
        'sigma_TC': sigma_TC,
        'delta_Yang': delta_Yang,
        'eps_Labusch': eps_Labusch,
    })


# ============================================================
# COMPUTE AND COMPARE
# ============================================================
print("=" * 70)
print("CORRECTED VLC SSS COMPUTATION")
print("=" * 70)

df = pd.read_csv(f'{DATA_DIR}/data_with_descriptors.csv')
vlc = df.apply(compute_vlc_corrected, axis=1)
df_aug = pd.concat([df, vlc], axis=1)

print(f"\nDataset: {len(df)} alloys, {len(df.dropna(subset=['YS']))} with YS data")

print(f"\n--- VLC SSS Statistics (CORRECTED) ---")
print(f"  sigma_y0 (T=0):    {df_aug['sigma_y0_VLC'].min():.1f} - {df_aug['sigma_y0_VLC'].max():.1f} MPa "
      f"(mean={df_aug['sigma_y0_VLC'].mean():.1f})")
print(f"  Delta_Eb (eV):     {df_aug['Delta_Eb_eV'].min():.4f} - {df_aug['Delta_Eb_eV'].max():.4f}")
print(f"  kT/Eb @ 300K:      {df_aug['kT_over_Eb'].min():.4f} - {df_aug['kT_over_Eb'].max():.4f}")
print(f"  T_correction:      {df_aug['T_correction'].min():.4f} - {df_aug['T_correction'].max():.4f}")
print(f"  sigma_y (300K):    {df_aug['sigma_y_VLC_300K'].min():.1f} - {df_aug['sigma_y_VLC_300K'].max():.1f} MPa "
      f"(mean={df_aug['sigma_y_VLC_300K'].mean():.1f})")
print(f"  sigma_Labusch:     {df_aug['sigma_Labusch'].min():.1f} - {df_aug['sigma_Labusch'].max():.1f} MPa "
      f"(mean={df_aug['sigma_Labusch'].mean():.1f})")
print(f"  sigma_TC:          {df_aug['sigma_TC'].min():.1f} - {df_aug['sigma_TC'].max():.1f} MPa "
      f"(mean={df_aug['sigma_TC'].mean():.1f})")

# Benchmark: CoCrFeMnNi (equimolar Cantor alloy)
cantor_mask = (
    (df_aug['Co_frac'].between(0.19, 0.21)) &
    (df_aug['Cr_frac'].between(0.19, 0.21)) &
    (df_aug['Fe_frac'].between(0.19, 0.21)) &
    (df_aug['Mn_frac'].between(0.19, 0.21)) &
    (df_aug['Ni_frac'].between(0.19, 0.21))
)
if cantor_mask.any():
    c_row = df_aug[cantor_mask].iloc[0]
    print(f"\n--- Benchmark: CoCrFeMnNi ---")
    print(f"  sigma_y0 (T=0): {c_row['sigma_y0_VLC']:.1f} MPa")
    print(f"  Delta_Eb:       {c_row['Delta_Eb_eV']:.4f} eV")
    print(f"  kT/Eb @ 300K:   {c_row['kT_over_Eb']:.4f}")
    print(f"  T_correction:   {c_row['T_correction']:.4f}")
    print(f"  sigma_y (300K): {c_row['sigma_y_VLC_300K']:.1f} MPa")
    print(f"  (Varvenne 2016 reports ~150-200 MPa with DFT inputs; expt σ_0 ~ 125 MPa)")
else:
    # Compute for synthetic equimolar CoCrFeMnNi
    synth = pd.Series({f'{el}_frac': 0.2 if el in ['Co','Cr','Fe','Mn','Ni'] else 0.0 for el in ELEMENTS})
    result = compute_vlc_corrected(synth, T=300)
    print(f"\n--- Benchmark: Equimolar CoCrFeMnNi (synthetic) ---")
    print(f"  sigma_y0 (T=0): {result['sigma_y0_VLC']:.1f} MPa")
    print(f"  Delta_Eb:       {result['Delta_Eb_eV']:.4f} eV")
    print(f"  kT/Eb @ 300K:   {result['kT_over_Eb']:.4f}")
    print(f"  T_correction:   {result['T_correction']:.4f}")
    print(f"  sigma_y (300K): {result['sigma_y_VLC_300K']:.1f} MPa")
    print(f"  (Varvenne 2016 reports ~150-200 MPa with DFT inputs; expt σ_0 ~ 125 MPa)")

# ============================================================
# COMPARISON WITH EXPERIMENTAL YS
# ============================================================
print("\n" + "=" * 70)
print("COMPARISON WITH EXPERIMENTAL YS")
print("=" * 70)

df_ys = df_aug.dropna(subset=['YS'])
y_exp = df_ys['YS'].values
n = len(y_exp)

for model_name, col in [('VLC (T=0)', 'sigma_y0_VLC'),
                          ('VLC (300K)', 'sigma_y_VLC_300K'),
                          ('Labusch', 'sigma_Labusch'),
                          ('Toda-Caraballo', 'sigma_TC')]:
    pred = df_ys[col].values
    r_val = np.corrcoef(pred, y_exp)[0, 1]
    raw_r2 = 1 - np.sum((y_exp - pred)**2) / np.sum((y_exp - np.mean(y_exp))**2)
    ratio = np.mean(pred) / np.mean(y_exp)
    print(f"\n  {model_name}:")
    print(f"    Mean predicted:  {np.mean(pred):.1f} MPa  (exp: {np.mean(y_exp):.1f})")
    print(f"    Pred/Exp ratio:  {ratio:.3f}")
    print(f"    Pearson r:       {r_val:.4f}")
    print(f"    Raw R²:          {raw_r2:.4f}")

# ============================================================
# LOO CROSS-VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("LOO CROSS-VALIDATION (Ridge, alpha=1.0)")
print("=" * 70)

models_to_test = {
    'Hall-Petch only':          ['d_inv_sqrt'],
    'VLC(0K) only':             ['sigma_y0_VLC'],
    'VLC(300K) only':           ['sigma_y_VLC_300K'],
    'Labusch only':             ['sigma_Labusch'],
    'TC only':                  ['sigma_TC'],
    'HP + VLC(0K)':             ['d_inv_sqrt', 'sigma_y0_VLC'],
    'HP + VLC(300K)':           ['d_inv_sqrt', 'sigma_y_VLC_300K'],
    'HP + Labusch':             ['d_inv_sqrt', 'sigma_Labusch'],
    'HP + TC':                  ['d_inv_sqrt', 'sigma_TC'],
    'Comp + HP':                [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt'],
    'Comp + HP + VLC(300K)':    [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'sigma_y_VLC_300K'],
    'Comp + HP + Labusch':      [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'sigma_Labusch'],
    'Comp + HP + TC':           [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'sigma_TC'],
    'Comp + HP + Process':      [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'ColdWork', 'RecrystT', 'HoldTime'],
    'Comp + HP + VLC + Proc':   [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'sigma_y_VLC_300K', 'ColdWork', 'RecrystT', 'HoldTime'],
    'Comp + HP + All SSS + Proc': [f'{el}_frac' for el in ELEMENTS] + ['d_inv_sqrt', 'sigma_y_VLC_300K', 'sigma_Labusch', 'sigma_TC', 'ColdWork', 'RecrystT', 'HoldTime'],
}

print(f"\n  {'Model':<35s} {'LOO R²':>8s} {'RMSE':>8s} {'MAE':>8s}")
print(f"  {'-' * 61}")

results = []
for mname, features in models_to_test.items():
    # Use frac columns
    feat_cols = []
    for f in features:
        if f in df_ys.columns:
            feat_cols.append(f)
        elif f.replace('_frac', '') + '_frac' in df_ys.columns:
            feat_cols.append(f.replace('_frac', '') + '_frac')

    df_clean = df_ys[feat_cols + ['YS']].replace([np.inf, -np.inf], np.nan).dropna()
    X = df_clean[feat_cols].values
    y = df_clean['YS'].values
    nn = len(y)

    scaler = StandardScaler()
    X_sc = scaler.fit_transform(X)

    preds = np.zeros(nn)
    for tr, te in LeaveOneOut().split(X_sc):
        lr = Ridge(alpha=1.0).fit(X_sc[tr], y[tr])
        preds[te] = lr.predict(X_sc[te])

    r2 = r2_score(y, preds)
    rmse = np.sqrt(mean_squared_error(y, preds))
    mae = np.mean(np.abs(y - preds))
    print(f"  {mname:<35s} {r2:>8.4f} {rmse:>8.1f} {mae:>8.1f}")
    results.append({'model': mname, 'R2': r2, 'RMSE': rmse, 'MAE': mae, 'n_feat': len(feat_cols)})

# ============================================================
# KEY QUESTION: Does VLC (corrected) add value over compositions?
# ============================================================
print("\n" + "=" * 70)
print("KEY QUESTION: Does corrected VLC add value over compositions alone?")
print("=" * 70)

# Compare: Comp+HP vs Comp+HP+VLC
for r in results:
    if r['model'] in ['Comp + HP', 'Comp + HP + VLC(300K)', 'Comp + HP + Process', 'Comp + HP + VLC + Proc']:
        print(f"  {r['model']:<35s}  LOO R² = {r['R2']:.4f}  (k={r['n_feat']})")

# ============================================================
# VLC vs other physics predictors: partial correlations
# ============================================================
print("\n" + "=" * 70)
print("PARTIAL CORRELATIONS: VLC vs compositions")
print("=" * 70)

from sklearn.linear_model import LinearRegression

# Residualize VLC on compositions
comp_cols = [f'{el}_frac' for el in ELEMENTS]
X_comp = df_ys[comp_cols].values
y_ys = df_ys['YS'].values

# VLC residual (what VLC knows that compositions don't)
lr_comp = LinearRegression().fit(X_comp, df_ys['sigma_y_VLC_300K'].values)
vlc_resid = df_ys['sigma_y_VLC_300K'].values - lr_comp.predict(X_comp)

# YS residual (what YS contains beyond compositions)
lr_ys = LinearRegression().fit(X_comp, y_ys)
ys_resid = y_ys - lr_ys.predict(X_comp)

partial_r = np.corrcoef(vlc_resid, ys_resid)[0, 1]
print(f"\n  Partial correlation (VLC|compositions, YS|compositions): {partial_r:.4f}")
print(f"  VLC residual variance: {np.var(vlc_resid):.2f}")
print(f"  Interpretation: VLC carries {'no' if abs(partial_r) < 0.1 else 'minimal' if abs(partial_r) < 0.2 else 'some'} "
      f"information beyond what compositions alone provide")

# Same for Labusch and TC
lr_lab = LinearRegression().fit(X_comp, df_ys['sigma_Labusch'].values)
lab_resid = df_ys['sigma_Labusch'].values - lr_lab.predict(X_comp)
partial_r_lab = np.corrcoef(lab_resid, ys_resid)[0, 1]

lr_tc = LinearRegression().fit(X_comp, df_ys['sigma_TC'].values)
tc_resid = df_ys['sigma_TC'].values - lr_tc.predict(X_comp)
partial_r_tc = np.corrcoef(tc_resid, ys_resid)[0, 1]

print(f"  Partial correlation (Labusch|comp, YS|comp): {partial_r_lab:.4f}")
print(f"  Partial correlation (TC|comp, YS|comp):      {partial_r_tc:.4f}")

# ============================================================
# WRITE OUT CORRECTED VALUES TO data_with_vlc.csv
# ============================================================
# Downstream analyses (sisso_analysis*, grain_size_scaling_analysis,
# exhaustive_model_search, external_validation, etc.) read this file.
# After the May 2026 SSS-formula corrections, regenerate it here.
# Hall-Petch-corrected experimental friction stress σ_0,exp = YS − k_HP·d^(-1/2)
# using Otto 2013's measured Cantor k_HP = 494 MPa·μm^(1/2). This anchors the
# grain-size subtraction to the same external reference (Otto's CoCrFeMnNi
# measurements) used to calibrate Z_TC and K_Lab, giving a single
# Cantor-anchored framework throughout.
k_HP_Cantor = 494.0  # MPa·μm^(1/2), Otto 2013
df_aug['sigma_0_exp'] = df_aug['YS'] - k_HP_Cantor * df_aug['d_inv_sqrt']

out_path = f'{DATA_DIR}/data_with_vlc.csv'
df_aug.to_csv(out_path, index=False)
print(f"\nWrote augmented data with corrected SSS to {out_path}")
print(f"  sigma_0_exp = YS - {k_HP_Cantor:.0f}·d^(-1/2) (Otto 2013 Cantor k_HP) added "
      f"(mean = {df_aug.dropna(subset=['YS'])['sigma_0_exp'].mean():.1f} MPa)")

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)
