# 00 — Data preparation

Turns the raw measurement workbook into the derived tables every later tier consumes.

| Script | Output | Role |
|---|---|---|
| `eda_analysis.py` | `data/derived/data_with_descriptors.csv`, EDA plots | Loads `data/raw/Grain_Size_Summary_v3.xlsx`, computes the 15 HEA descriptors, property distributions, correlation matrix (paper SI §S1) |
| `vlc_corrected.py` | `data/derived/data_with_vlc.csv` | VLC/Labusch/Toda-Caraballo SSS predictions per alloy (SI §S3 formulations) |
| `eda_diagnostics.py` | `results/eda_diagnostics_summary.txt`, hull/heatmap figures | Pre-modeling diagnostics: sigma0/k_HP identifiability, batch hull overlap, noise ceiling (SI §S2) |
| `build_armote_inputs.py` | `data/derived/inputs.csv` + feature manifest | Assembles the shared S1–S4 feature ladder used by every model family (paper Table 2) |

Run order: `eda_analysis.py` → `vlc_corrected.py` → `build_armote_inputs.py` (or `make data`).
