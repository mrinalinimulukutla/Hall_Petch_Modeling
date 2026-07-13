#!/usr/bin/env python3
"""Generate Figure 1 (Sample provenance) for the Hall-Petch paper.

Layout:
  (a) Per-element composition distribution per batch (8 sub-panels, one per
      element). Each sub-panel shows the at.% spread of that element across
      the 6 batches. The Al = Cu = 0 constraint of the C campaign is
      immediately visible from the raw at.% axes.
  (b) Processing-parameter coverage (cold work vs. recrystallization
      temperature). The B campaign collapses to (60%, 950 deg C); the C
      campaign fans across the cold-work x temperature grid.
"""
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from _config import REPO_ROOT, DATA_DIR, RAW_DATA_DIR, RESULTS_DIR, PLOTS_DIR, PAPER_DIR, PAPER_FIG_DIR
BASE = str(REPO_ROOT)
OUT = f"{PAPER_FIG_DIR}/fig_provenance.png"

ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]
BATCHES = ["BBA", "BBB", "BBC", "CBA", "CBB", "CBC"]

BATCH_COLORS = {
    "BBA": "#1f4e79", "BBB": "#2e75b6", "BBC": "#5b9bd5",
    "CBA": "#a5392c", "CBB": "#c55a11", "CBC": "#ed7d31",
}
MARKERS = {"BBA": "o", "BBB": "s", "BBC": "^",
           "CBA": "o", "CBB": "s", "CBC": "^"}

df = pd.read_csv(f"{DATA_DIR}/data_with_descriptors.csv").dropna(subset=["YS"]).reset_index(drop=True)
print(f"Loaded {len(df)} alloys ({df['Iteration'].nunique()} batches)")

fig = plt.figure(figsize=(14, 5.8))
gs = GridSpec(2, 5, figure=fig, width_ratios=[1, 1, 1, 1, 2.4],
              hspace=0.55, wspace=0.45)

# -------- Panels a1-a8: per-element distributions --------
for i, el in enumerate(ELEMENTS):
    r, c = i // 4, i % 4
    ax = fig.add_subplot(gs[r, c])
    np.random.seed(i)
    for j, batch in enumerate(BATCHES):
        m = df["Iteration"].values == batch
        if not m.any():
            continue
        vals = df.loc[m, el].values
        x_jitter = j + np.random.uniform(-0.22, 0.22, len(vals))
        ax.scatter(x_jitter, vals, c=BATCH_COLORS[batch], marker=MARKERS[batch],
                   s=24, alpha=0.85, edgecolors="k", linewidth=0.3)
    ax.set_xticks(range(len(BATCHES)))
    ax.set_xticklabels(BATCHES, rotation=45, fontsize=8)
    ax.set_ylabel("at.%", fontsize=9)
    ax.set_title(el, fontsize=10, fontweight="bold")
    ax.grid(True, alpha=0.25, axis="y")
    ax.tick_params(axis="y", labelsize=8)
    # Divider between B and C campaigns
    ax.axvline(2.5, color="gray", lw=0.6, ls="--", alpha=0.55)

# Title spanning the composition panels
fig.text(0.005, 1.005, r"$\bf{(a)}$  Composition coverage by element and batch",
         fontsize=11, ha="left", va="top")

# -------- Panel b: processing space --------
ax = fig.add_subplot(gs[:, 4])
np.random.seed(0)
cw_jitter = np.random.uniform(-0.6, 0.6, len(df))
t_jitter = np.random.uniform(-12, 12, len(df))

for batch in BATCHES:
    m = df["Iteration"].values == batch
    if not m.any():
        continue
    cw = df.loc[m, "ColdWork"].values + cw_jitter[m]
    t = df.loc[m, "RecrystT"].values + t_jitter[m]
    ax.scatter(cw, t, c=BATCH_COLORS[batch], marker=MARKERS[batch],
               s=70, alpha=0.85, edgecolors="k", linewidth=0.5,
               label=f"{batch} ($n$={m.sum()})")

ax.annotate("B campaign:\nfixed (60%, 950 °C, 0.5 h)",
            xy=(60, 950), xytext=(43, 1180),
            fontsize=9, ha="left", color="#1f4e79", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#1f4e79", alpha=0.7))
ax.annotate("C campaign:\nvaried (CW, $T_{\\mathrm{rx}}$, hold time)",
            xy=(50, 780), xytext=(36.5, 620),
            fontsize=9, ha="left", color="#a5392c", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="#a5392c", alpha=0.7))

ax.set_xlabel("Cold work (%)", fontsize=10)
ax.set_ylabel(r"Recrystallization temperature $T_{\mathrm{rx}}$ ($^{\circ}$C)", fontsize=10)
ax.set_title(r"$\bf{(b)}$  Processing coverage", fontsize=11, loc="left", pad=8)
ax.set_xlim(35, 65)
ax.set_ylim(580, 1320)
ax.set_xticks([40, 50, 60])
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8, loc="lower right", ncol=2, framealpha=0.9)

plt.savefig(OUT, dpi=200, bbox_inches="tight")
plt.close()
print(f"Saved: {OUT}")
