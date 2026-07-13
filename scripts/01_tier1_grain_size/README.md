# 01 — Tier 1: grain size only

The universal backbone: how far does grain size alone go? (Paper §4.1)

| Script | Output | Role |
|---|---|---|
| `grain_size_scaling_analysis.py` | scaling-law CSVs + fit figures | Nine scaling laws for YS and HV, AIC/AICc/BIC ranking |
| `bayesian_scaling_analysis.py` | `results/bayesian_model_comparison.csv` | PyMC posteriors + PSIS-LOO stacking; free-exponent posterior |
| `eda_within_replicate_kHP.py` | `results/within_replicate_kHP_summary.txt` | Within-composition-replicate Hall–Petch fits (SI §S4) |
| `literature_kHP_table.py` | `results/literature_kHP_table.csv` | Literature k_HP comparison (SI Table S10) |
