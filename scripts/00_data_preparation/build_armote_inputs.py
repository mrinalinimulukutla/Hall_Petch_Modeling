#!/usr/bin/env python3
"""
Build a single ARMOTE input file: grain-size summary + all S1-S5 features.
==========================================================================

Produces data/derived/inputs.csv — the grain-size-summary rows with every
feature from the S1-S5 ladder appended, ready to feed the ARMOTE non-linear
panel (scripts/exhaustive_model_search.py).

Feature blocks (cumulative ladder S1-S4; S5 is NOT a feature block):
  S1 grain     : d_inv_sqrt, SD_GS
  S2 Wen       : curated Wen descriptors (VEC, dH_mix, dS_mix, Omega, delta_chi, delta)
  S3 processing: ColdWork, RecrystT, HoldTime
  S4 comp+SSS  : 8 composition fractions + SSS sigma (VLC, Labusch, Toda-Caraballo)
                 + the two SSS misfit descriptors (Phi_VLC, eps_Labusch)

NOTE: in the revised ladder S5 is SYMBOLIC REGRESSION (PySR/SISSO discover the
interactions), NOT a feature set. Hand-engineered interaction columns are
therefore intentionally OMITTED from this file; ARMOTE runs on S1-S4.

The curated-Wen descriptors and the SSS sigma values are the CANONICAL computed
values from the repo pipeline (vlc_corrected.py -> data/derived/data_with_vlc.csv),
so the metallurgical constants in CLAUDE.md (Co shear 75 GPa, gamma-Fe a=3.590 A,
Mn radius 127 pm, sphere-volume Phi_VLC) are respected. The S5 interaction terms
are engineered here exactly as in scripts/fair_comparison.py.

Outputs:
  data/derived/inputs.csv                  (the ARMOTE input file)
  data/derived/inputs_feature_manifest.csv (column -> S-block map for config)
"""
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/ (for _config)
from _config import DATA_DIR

ELEMENTS = ['Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'Ni', 'V']

# ---- load the canonical derived data (grain-size summary + descriptors) ----
df = pd.read_csv(f'{DATA_DIR}/data_with_vlc.csv')
df = df.loc[:, ~df.columns.duplicated()].copy()
df['Omega'] = df['Omega'].clip(upper=100)
df = df.replace([np.inf, -np.inf], np.nan)
df['d_inv_sqrt'] = df['GrainSize'].values ** -0.5

# ---- column groups ----------------------------------------------------------
META    = ['Iteration', 'Alloy']                    # Iteration = BO batch = LOBO cluster
RAW     = ELEMENTS + ['GrainSize']                  # raw at.% + mean grain size (reference)
TARGETS = ['YS', 'SD_YS', 'HV', 'SD_HV']

S1_grain = ['d_inv_sqrt', 'SD_GS']
S2_wen   = ['VEC', 'dH_mix', 'dS_mix', 'Omega', 'delta_chi', 'delta']
S3_proc  = ['ColdWork', 'RecrystT', 'HoldTime']
S4_comp  = [f'{el}_frac' for el in ELEMENTS]
S4_sss   = ['sigma_y0_VLC', 'sigma_Labusch', 'sigma_TC', 'Phi_VLC', 'eps_Labusch']

BLOCKS = [
    ('meta', META), ('raw', RAW), ('target', TARGETS),
    ('S1_grain', S1_grain), ('S2_wen', S2_wen), ('S3_proc', S3_proc),
    ('S4_comp', S4_comp), ('S4_sss', S4_sss),
]

ordered_cols, manifest = [], []
for block, cols in BLOCKS:
    for c in cols:
        if c not in df.columns:
            raise KeyError(f'missing expected column: {c}')
        if c not in ordered_cols:          # de-dup (SD_GS only once, in S1)
            ordered_cols.append(c)
            manifest.append({'column': c, 'block': block})

inputs = df[ordered_cols].copy()
out_csv = f'{DATA_DIR}/inputs.csv'
inputs.to_csv(out_csv, index=False)
pd.DataFrame(manifest).to_csv(f'{DATA_DIR}/inputs_feature_manifest.csv', index=False)

# ---- report -----------------------------------------------------------------
print('=' * 68)
print('ARMOTE INPUT FILE BUILT')
print('=' * 68)
print(f'rows: {len(inputs)}  (YS non-null: {inputs.YS.notna().sum()}, '
      f'HV non-null: {inputs.HV.notna().sum()})')
print(f'total columns: {len(ordered_cols)}')
nfeat = sum(len(cols) for b, cols in BLOCKS if b.startswith('S'))
print(f'modeling features (S1-S5): {nfeat}')
print()
for block, cols in BLOCKS:
    if block.startswith('S'):
        print(f'  {block:12s} ({len(cols):2d}): {", ".join(cols)}')
print()
print(f'Wrote: {out_csv}')
print(f'Wrote: {DATA_DIR}/inputs_feature_manifest.csv')
# quick sanity on the calculated descriptors
print('\nSanity (first alloy):')
r = inputs.iloc[0]
print(f'  {r.Alloy}: VEC={r.VEC:.2f} dS_mix={r.dS_mix:.2f} delta_chi={r.delta_chi:.4f} '
      f'sigma_y0_VLC={r.sigma_y0_VLC:.1f} sigma_Labusch={r.sigma_Labusch:.1f} sigma_TC={r.sigma_TC:.1f}')
