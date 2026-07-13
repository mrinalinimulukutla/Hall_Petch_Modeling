#!/usr/bin/env python3
"""Replot the fair-comparison LOBO heatmap with plain, self-explanatory labels.
Reads results/fair_comparison.csv (no model re-run). Replaces the S1-S4 codenames
with feature descriptions on the x-axis.
Output: analysis_plots/fair_comparison_LOBO_heatmap.png
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _config import RESULTS_DIR, PLOTS_DIR

# plain descriptions for the feature ladder (no codenames)
SET_LABEL = {
    'S1_grain':    'grain only\n(d⁻¹ᐟ², SD)',
    'S2_wen':      '+ Wen\ndescriptors',
    'S3_wen_proc': '+ processing',
    'S4_phys':     '+ composition\n+ SSS',
}
LADDER = ['S1_grain', 'S2_wen', 'S3_wen_proc', 'S4_phys']

df = pd.read_csv(f'{RESULTS_DIR}/fair_comparison.csv')
fig, axes = plt.subplots(1, 2, figsize=(16, 7))
for ax, tgt in zip(axes, ['YS', 'HV']):
    rdf = df[df.Target == tgt]
    piv = rdf.pivot_table(index='Model', columns='FeatureSet', values='R2_LOBO').reindex(columns=LADDER)
    order = rdf.groupby('Model')['R2_LOBO'].max().sort_values(ascending=False).index.tolist()
    piv = piv.reindex(order)
    im = ax.imshow(piv.values, cmap='RdYlGn', vmin=0, vmax=0.8, aspect='auto')
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels([SET_LABEL[c] for c in piv.columns], fontsize=10)
    ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index, fontsize=10)
    fam = rdf.set_index('Model')['Family'].to_dict()
    for i, m in enumerate(piv.index):
        ax.get_yticklabels()[i].set_color('#1F3A5F' if fam.get(m) == 'linear' else '#C84B31')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=8,
                        color='black' if v > 0.3 else 'white')
    ax.set_title(f'{tgt}: cross-cluster (LOBO) R²\nblue = linear models, red = non-linear', fontsize=12, weight='bold')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='LOBO R²')
plt.tight_layout()
out = f'{PLOTS_DIR}/fair_comparison_LOBO_heatmap.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
print('Wrote', out)
