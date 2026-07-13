# 04 — Tier 4: non-linear ML

Does flexibility pay off cross-cluster? (Paper §4.4)

| Script | Output | Role |
|---|---|---|
| `exhaustive_model_search.py` | `results/model_search_results*.csv` | Legacy 17-model panel (Optuna-tuned) — the validation-failure exhibit |
| `xgboost_shap_analysis.py` | SHAP figures | Feature-importance analysis of the best tree model (SI §S5) |
| `fair_comparison.py` | `results/fair_comparison*.csv` + LOBO heatmaps | Equal-footing zero-tuning panel on identical ladders/splits |
| `armote_ladder_cv.py` | `results/armote_ladder_cv.csv` | S1–S4 ladder summary; full nested-CV ARMOTE outputs archived separately |
