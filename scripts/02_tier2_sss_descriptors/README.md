# 02 — Tier 2: SSS physics descriptors

Faithful physics models as predictors and as features; the redundancy audit. (Paper §4.2)

| Script | Output | Role |
|---|---|---|
| `vlc_sss_analysis.py` | SSS benchmark CSVs + parity figure | Cantor-anchored VLC/Labusch/TC audit; standalone, +HP, and partial-r redundancy tests |
| `pca_ols_analysis.py` | `results/pca_ols_results.csv`, loadings/importance figures | PCA-OLS on curated Wen + SD_grain; reconstructed importances (paper §4.6) |
