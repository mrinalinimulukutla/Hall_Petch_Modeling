# 06 — Validation floor

The protocols that run under every tier. (Paper §3.4, §4.5, §4.8)

| Script | Output | Role |
|---|---|---|
| `cv_comparison.py` | `results/cv_comparison.csv` | 5-fold vs LOO vs LOBO for headline models |
| `external_validation.py` | `results/external_validation_results.csv` | 82 literature points, tiered sources |
| `pysr_external_validation.py` | `results/pysr_external_validation.csv` | Every PySR grid equation scored externally |
| `singularity_audit.py` | `results/singularity_audit.csv` | Pole detection + deployment envelopes for all compact equations |
| `bootstrap_sr_constants.py` | `results/bootstrap_sr_constants.csv` | Bootstrap CIs on every free constant |
| `per_batch_lobo.py` | `results/per_batch_lobo.csv` | Per-batch LOBO + hull containment (SI Table S11) |
| `mc_grain_size_sensitivity.py` | `results/mc_grain_size_sensitivity.csv` | Measurement-uncertainty propagation |
| `vif_diagnostics.py` | `results/vif_diagnostics.csv` | Collinearity diagnostics across feature sets |
| `variance_ceiling.py` | `results/variance_ceiling.csv` | Noise-limited R² ceiling |
| `unified_model_table.py` | `results/unified_model_table.csv` | One table, every model, five columns (LOO/LOBO/BIC/ext/safe) |
| `review_diagnostics.py` | `results/review_diagnostics_summary.csv` | Referee-response diagnostics bundle |
