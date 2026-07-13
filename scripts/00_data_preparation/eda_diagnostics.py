#!/usr/bin/env python3
"""
Pre-modeling EDA diagnostics for the Hall-Petch HEA dataset.

Three diagnostics that should run BEFORE any targeted regression:
  [1] Composition x grain-size confounding
      -> Is the sigma_0(comp) + k_HP * d^(-1/2) split identifiable?
  [2] Batch x composition coverage in PCA space
      -> Does LOBO test extrapolation, or is it effectively in-distribution?
  [3] Pseudo-replicate variance floor + measurement-noise floor
      -> What R^2 ceiling does the data noise structure permit?

Outputs:
  - analysis_plots/71_comp_gs_confounding.png
  - analysis_plots/72_batch_pca_coverage.png
  - analysis_plots/73_pseudoreplicate_variance.png
  - eda_diagnostics_summary.txt
"""
import warnings

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # scripts/ (for _config)
from _config import REPO_ROOT, DATA_DIR, RAW_DATA_DIR, RESULTS_DIR, PLOTS_DIR, PAPER_DIR, PAPER_FIG_DIR
BASE = str(REPO_ROOT)
PLOT_DIR = f"{PLOTS_DIR}"
DATA_CSV = f"{DATA_DIR}/data_with_descriptors.csv"

ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]
BATCHES = ["BBA", "BBB", "BBC", "CBA", "CBB", "CBC"]
BATCH_COLORS = dict(zip(BATCHES, plt.cm.tab10(np.linspace(0, 1, len(BATCHES)))))

df = pd.read_csv(DATA_CSV)
df = df.dropna(subset=["YS"]).reset_index(drop=True)
n = len(df)

summary_lines = []


def log(msg=""):
    print(msg)
    summary_lines.append(msg)


log("=" * 72)
log("PRE-MODELING EDA DIAGNOSTICS — Hall-Petch HEA dataset")
log("=" * 72)
log(f"Loaded {n} alloys with YS, {df['Iteration'].nunique()} batches.")

# ============================================================
# [1] Composition x grain-size confounding
# ============================================================
log("\n[1] COMPOSITION x GRAIN-SIZE CONFOUNDING")
log("-" * 72)

fig, axes = plt.subplots(2, 4, figsize=(18, 9))
results_1 = []
for i, el in enumerate(ELEMENTS):
    ax = axes[i // 4, i % 4]
    for batch in BATCHES:
        m = df["Iteration"] == batch
        if m.sum() == 0:
            continue
        ax.scatter(
            df.loc[m, el],
            df.loc[m, "GrainSize"],
            c=[BATCH_COLORS[batch]],
            label=batch,
            s=40,
            alpha=0.7,
            edgecolors="k",
            linewidth=0.4,
        )
    r, p = stats.pearsonr(df[el], df["GrainSize"])
    rs, ps = stats.spearmanr(df[el], df["GrainSize"])
    results_1.append((el, r, p, rs, ps))
    ax.set_xlabel(f"{el} (at.%)", fontsize=11)
    ax.set_ylabel("Grain Size (μm)", fontsize=11)
    flag = " *" if abs(r) > 0.3 else ""
    ax.set_title(
        f"{el}: Pearson r={r:+.2f}, Spearman ρ={rs:+.2f}{flag}", fontsize=10
    )
    ax.grid(True, alpha=0.3)
    if i == 0:
        ax.legend(fontsize=8, loc="best")
plt.suptitle(
    "Composition × Grain-Size Confounding (per element, batch-coded)", fontsize=14
)
plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/71_comp_gs_confounding.png", dpi=150)
plt.close()
log("Saved: analysis_plots/71_comp_gs_confounding.png")

log(f"\n{'Element':>8s} {'Pearson r':>11s} {'p':>10s} {'Spearman ρ':>11s} {'p_s':>10s}")
for el, r, p, rs, ps in results_1:
    flag = " ***" if abs(r) > 0.3 else ""
    log(f"{el:>8s} {r:>+11.3f} {p:>10.2e} {rs:>+11.3f} {ps:>10.2e}{flag}")
log("(*** = |r| > 0.3, suggests non-trivial composition-grain-size correlation)")

X_comp = df[ELEMENTS].values
y_gs = df["GrainSize"].values
y_dinv = df["d_inv_sqrt"].values
r2_gs_comp = LinearRegression().fit(X_comp, y_gs).score(X_comp, y_gs)
r2_dinv_comp = LinearRegression().fit(X_comp, y_dinv).score(X_comp, y_dinv)
log(f"\nJoint regression: R²(GrainSize ~ all 8 comp fractions) = {r2_gs_comp:.3f}")
log(f"                  R²(d^(-1/2)  ~ all 8 comp fractions) = {r2_dinv_comp:.3f}")
log(f"  → {r2_dinv_comp*100:.1f}% of d^(-1/2) variance is predictable from composition.")
log(f"  → Implied VIF(d^(-1/2) | comp) ≈ {1/(1-r2_dinv_comp):.1f}")
log("  → Higher value ⇒ weaker identifiability of σ₀(comp) vs k_HP·d^(-1/2) split.")

# Add processing variables
PROC = ["ColdWork", "RecrystT", "HoldTime"]
X_full = df[ELEMENTS + PROC].values
r2_dinv_full = LinearRegression().fit(X_full, y_dinv).score(X_full, y_dinv)
log(f"\nWith processing added: R²(d^(-1/2) ~ comp + proc) = {r2_dinv_full:.3f}")
log(f"  → {(1-r2_dinv_full)*100:.1f}% of d^(-1/2) variance is genuinely independent of comp+proc.")

# ============================================================
# [2] Batch x composition coverage in PCA space
# ============================================================
log("\n\n[2] BATCH × COMPOSITION COVERAGE")
log("-" * 72)

scaler = StandardScaler()
X_std = scaler.fit_transform(df[ELEMENTS].values)
pca = PCA(n_components=8)
PC = pca.fit_transform(X_std)
evr = pca.explained_variance_ratio_
cum = np.cumsum(evr)
log(f"PCA explained variance: {[f'{v:.3f}' for v in evr]}")
log(f"Cumulative:             {[f'{v:.3f}' for v in cum]}")
n_eff_dim = int((cum < 0.95).sum() + 1)
log(f"Effective dimensionality (≥95% var): {n_eff_dim} of 8")

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# (A) PC1 vs PC2 colored by batch
ax = axes[0]
for batch in BATCHES:
    m = df["Iteration"].values == batch
    if m.sum() == 0:
        continue
    ax.scatter(
        PC[m, 0],
        PC[m, 1],
        c=[BATCH_COLORS[batch]],
        label=f"{batch} (n={m.sum()})",
        s=60,
        alpha=0.7,
        edgecolors="k",
        linewidth=0.5,
    )
ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)", fontsize=11)
ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)", fontsize=11)
ax.set_title("Composition PCA — batch coverage", fontsize=12)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# (B) Convex hulls per batch
ax = axes[1]
for batch in BATCHES:
    m = df["Iteration"].values == batch
    if m.sum() < 3:
        continue
    pts = PC[m, :2]
    try:
        hull = ConvexHull(pts)
        hp = np.append(hull.vertices, hull.vertices[0])
        ax.plot(
            pts[hp, 0],
            pts[hp, 1],
            "-",
            c=BATCH_COLORS[batch],
            lw=2,
            label=batch,
        )
        ax.fill(pts[hp, 0], pts[hp, 1], c=BATCH_COLORS[batch], alpha=0.15)
    except Exception:
        pass
    ax.scatter(pts[:, 0], pts[:, 1], c=[BATCH_COLORS[batch]], s=20, alpha=0.6)
ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)", fontsize=11)
ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)", fontsize=11)
ax.set_title("Batch convex hulls in composition PCA", fontsize=12)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# Pairwise hull-overlap matrix: fraction of batch j's points inside hull of batch i
overlap = np.full((len(BATCHES), len(BATCHES)), np.nan)
hulls = {}
for i_b, b in enumerate(BATCHES):
    m = df["Iteration"].values == b
    if m.sum() < 3:
        continue
    try:
        hulls[b] = ConvexHull(PC[m, :2])
        hulls[b]._pts = PC[m, :2]
    except Exception:
        pass

from matplotlib.path import Path

for i, bi in enumerate(BATCHES):
    if bi not in hulls:
        continue
    verts = hulls[bi]._pts[hulls[bi].vertices]
    path = Path(verts)
    for j, bj in enumerate(BATCHES):
        m_j = df["Iteration"].values == bj
        if m_j.sum() == 0:
            continue
        pts_j = PC[m_j, :2]
        inside = path.contains_points(pts_j)
        overlap[i, j] = inside.mean()

# (C) Heatmap of pairwise overlap
ax = axes[2]
im = ax.imshow(overlap, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(BATCHES)))
ax.set_yticks(range(len(BATCHES)))
ax.set_xticklabels(BATCHES)
ax.set_yticklabels(BATCHES)
ax.set_xlabel("Test batch (j)", fontsize=11)
ax.set_ylabel("Hull batch (i)", fontsize=11)
ax.set_title(
    "Frac. of batch-j points inside\nconvex hull of batch-i (PC1-PC2)", fontsize=11
)
for i in range(len(BATCHES)):
    for j in range(len(BATCHES)):
        v = overlap[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9)
plt.colorbar(im, ax=ax, fraction=0.04)

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/72_batch_pca_coverage.png", dpi=150)
plt.close()
log("Saved: analysis_plots/72_batch_pca_coverage.png")

# Summarize: mean of off-diagonal overlap, and per-batch max-overlap
off_diag = overlap.copy()
np.fill_diagonal(off_diag, np.nan)
mean_off = np.nanmean(off_diag)
log(f"\nMean off-diagonal overlap: {mean_off:.2f}")
log("  (1.0 = batches fully overlap in composition PCA;")
log("   0   = fully disjoint -> LOBO is genuine extrapolation)")
log("\nPer-batch worst-case coverage when held out:")
log(f"  {'Held-out':>9s} {'max(P inside other hulls)':>30s}")
for j, b in enumerate(BATCHES):
    col = overlap[:, j].copy()
    col[j] = np.nan
    cov = np.nanmax(col) if np.isfinite(col).any() else np.nan
    log(f"  {b:>9s} {cov:>30.2f}")
log("  → Low value ⇒ when this batch is held out (LOBO), its composition region")
log("    is poorly covered by training batches.")

# ============================================================
# [3] Pseudo-replicate variance floor + measurement noise floor
# ============================================================
log("\n\n[3] PSEUDO-REPLICATE & MEASUREMENT-NOISE VARIANCE FLOOR")
log("-" * 72)

# Group alloys by exact composition tuple
df = df.assign(_compkey=df[ELEMENTS].apply(lambda r: tuple(r.values), axis=1))
groups = df.groupby("_compkey")
group_sizes = groups.size()
n_unique = groups.ngroups
n_replicate_groups = (group_sizes >= 2).sum()
n_replicate_alloys = group_sizes[group_sizes >= 2].sum()

log(f"Unique compositions: {n_unique}")
log(f"  - singletons (1 alloy):  {(group_sizes == 1).sum()}")
log(f"  - replicate groups (≥2): {n_replicate_groups}  containing {n_replicate_alloys} alloys")
log(f"  - pseudo-replicate fraction: {n_replicate_alloys/n*100:.1f}%")

within_sds = []
within_means = []
within_gs_ranges = []
ss_within = 0.0           # within-group SS, summed across all groups (singletons contribute 0)
df_within = 0
for k, g in groups:
    if len(g) >= 2:
        within_sds.append(g["YS"].std(ddof=1))
        within_means.append(g["YS"].mean())
        within_gs_ranges.append(g["GrainSize"].max() - g["GrainSize"].min())
    ss_within += ((g["YS"] - g["YS"].mean()) ** 2).sum()  # 0 for singletons
    df_within += len(g) - 1

within_sds = np.array(within_sds)
within_means = np.array(within_means)
within_gs_ranges = np.array(within_gs_ranges)

total_var = df["YS"].var(ddof=1)
total_ss = total_var * (n - 1)
# Composition-only R^2 ceiling: a perfect composition-mean predictor leaves only
# the within-group SS as residual.
ceiling_comp_only = 1.0 - ss_within / total_ss
ms_within = ss_within / df_within if df_within > 0 else np.nan

# Measurement noise floor from SD_YS column (per-alloy replicate-measurement SD)
sd_ys = df["SD_YS"].dropna().values
if len(sd_ys) > 0:
    mean_sd2 = np.mean(sd_ys**2)
    rms_sd = np.sqrt(mean_sd2)
    ceiling_full_model = 1.0 - mean_sd2 / total_var
else:
    mean_sd2 = np.nan
    rms_sd = np.nan
    ceiling_full_model = np.nan

log(f"\nVariance decomposition:")
log(f"  Total YS variance σ²_total = {total_var:.0f} MPa²  (SD = {np.sqrt(total_var):.1f} MPa)")
log(f"  Pooled within-comp variance σ²_w = {ms_within:.0f} MPa²  (SD = {np.sqrt(ms_within):.1f} MPa)")
log(f"  Mean per-alloy measurement variance ⟨SD_YS²⟩ = {mean_sd2:.0f} MPa²")
log(f"    (rms of SD_YS = {rms_sd:.1f} MPa, n={len(sd_ys)} alloys with SD_YS reported)")
log(f"\nR² ceilings:")
log(f"  Composition-only model:         R² ≤ {ceiling_comp_only:.3f}")
log(f"    (1 − σ²_within / σ²_total — within-comp variance includes HP grain-size effect)")
log(f"  Composition + grain-size model: R² ≤ {ceiling_full_model:.3f}")
log(f"    (1 − ⟨SD_YS²⟩ / σ²_total — pure measurement-noise floor)")
log(f"\nReality check vs. paper:")
log(f"  XGBoost LOO R² = 0.729   →  {(0.729/ceiling_full_model)*100:.0f}% of full-model ceiling")
log(f"  M3 LOO R²      = 0.652   →  {(0.652/ceiling_full_model)*100:.0f}% of full-model ceiling")
log(f"  SISSO LOO R²   = 0.671   →  {(0.671/ceiling_full_model)*100:.0f}% of full-model ceiling")

# Plot
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# (A) Group-size histogram
ax = axes[0]
ax.hist(
    group_sizes.values,
    bins=range(1, group_sizes.max() + 2),
    edgecolor="k",
    alpha=0.7,
    color="steelblue",
)
ax.set_xlabel("Number of alloys per unique composition", fontsize=11)
ax.set_ylabel("Number of composition groups", fontsize=11)
ax.set_title(
    f"Composition replication\n({n_unique} unique compositions; "
    f"{n_replicate_alloys}/{n} alloys are pseudo-replicates)",
    fontsize=11,
)
ax.grid(True, alpha=0.3)

# (B) Within-group YS SD vs within-group GS range
ax = axes[1]
ax.scatter(
    within_gs_ranges, within_sds, s=60, alpha=0.7, edgecolors="k", linewidth=0.5
)
ax.axhline(rms_sd, color="orange", ls="--", lw=1.5, label=f"⟨SD_YS²⟩^½ = {rms_sd:.1f} MPa")
ax.set_xlabel("Within-group ΔGrainSize (μm)", fontsize=11)
ax.set_ylabel("Within-group YS SD (MPa)", fontsize=11)
ax.set_title(
    "Within-comp YS scatter vs. ΔGS\n"
    "(if independent of ΔGS → measurement noise; otherwise → HP effect)",
    fontsize=11,
)
ax.grid(True, alpha=0.3)
if len(within_gs_ranges) >= 3:
    slope, intercept, r_v, p_v, _ = stats.linregress(within_gs_ranges, within_sds)
    xfit = np.linspace(0, within_gs_ranges.max(), 100)
    ax.plot(
        xfit, slope * xfit + intercept, "r--", lw=1.5,
        label=f"r={r_v:+.2f}, p={p_v:.2g}",
    )
ax.legend(fontsize=9)

# (C) Variance decomposition bar
ax = axes[2]
labels = [
    "Total σ²_YS",
    "Within-comp σ²_w",
    "⟨SD_YS²⟩\n(measurement)",
]
values = [total_var, ms_within, mean_sd2]
colors = ["gray", "firebrick", "darkorange"]
bars = ax.bar(labels, values, color=colors, edgecolor="k")
for bar, v in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        v,
        f"{v:.0f}",
        ha="center",
        va="bottom",
        fontsize=10,
    )
ax.set_ylabel("Variance (MPa²)", fontsize=11)
ax.set_title(
    f"Variance decomposition\n"
    f"R² ceiling: comp-only ≈ {ceiling_comp_only:.3f}, "
    f"full ≈ {ceiling_full_model:.3f}",
    fontsize=11,
)
ax.grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig(f"{PLOT_DIR}/73_pseudoreplicate_variance.png", dpi=150)
plt.close()
log("Saved: analysis_plots/73_pseudoreplicate_variance.png")

# ============================================================
# Final summary
# ============================================================
log("\n\n" + "=" * 72)
log("SUMMARY")
log("=" * 72)
sorted_results = sorted(results_1, key=lambda x: -abs(x[1]))
log("[1] Strongest composition × grain-size correlations:")
for el, r, p, rs, ps in sorted_results[:3]:
    log(f"      {el}: Pearson r={r:+.2f} (p={p:.2g})")
log(f"    Joint R²(d^(-1/2) ~ comp)         = {r2_dinv_comp:.3f}")
log(f"    Joint R²(d^(-1/2) ~ comp + proc)  = {r2_dinv_full:.3f}")
log(
    f"    ⇒ ~{r2_dinv_full*100:.0f}% of d^(-1/2) variance is captured by composition+processing,"
)
log(f"      so the σ₀(comp) vs k_HP·d^(-1/2) split has limited identifiability.")
log("")
log("[2] Batch coverage in composition PCA:")
log(f"    Mean off-diagonal hull overlap = {mean_off:.2f}  (0=disjoint, 1=identical)")
log(f"    Effective dim. of comp space (≥95% var) = {n_eff_dim} of 8")
log("    ⇒ See heatmap (fig 72) for which batches are reachable from which.")
log("")
log(f"[3] R² ceilings:")
log(f"    Composition-only models:   ≤ {ceiling_comp_only:.3f}")
log(f"    Composition + grain size:  ≤ {ceiling_full_model:.3f}  (measurement-noise floor)")
log(f"    ⇒ XGBoost (0.729) is at {(0.729/ceiling_full_model)*100:.0f}% of the noise floor.")
log(f"    Pseudo-replicate fraction = {n_replicate_alloys/n*100:.1f}%")
log("=" * 72)

with open(f"{RESULTS_DIR}/eda_diagnostics_summary.txt", "w") as f:
    f.write("\n".join(summary_lines) + "\n")
log("\nSaved: eda_diagnostics_summary.txt")
