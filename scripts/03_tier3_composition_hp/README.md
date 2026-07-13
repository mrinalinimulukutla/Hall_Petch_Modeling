# 03 — Tier 3: composition-dependent Hall–Petch (M-models)

Where the YS signal lives: sigma0(comp) + k·d^-1/2, and the SD_grain extension. (Paper §4.3)

| Script | Output | Role |
|---|---|---|
| `composition_hp_analysis.py` | `results/comp_hp_model_comparison.csv` | M0–M12 hierarchy, LOO/LOBO/BIC + Bayesian stacking |
| `kHP_composition_analysis.py` | two-stage k_eff results | Tests composition dependence of the slope (R² = 0.006) |
| `sdgrain_model_comparison.py` | `results/sdgrain_model_comparison.csv` | SD_grain-augmented models (M13, M15) vs the baseline hierarchy |
| `export_fitted_models.py` | `results/m3_model.pkl`, coefficient CSVs | Pins headline coefficients; CI asserts these values |
