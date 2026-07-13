# 05 — Tier 5: symbolic regression

Discovery of closed-form laws — and the deployment failure mode. (Paper §4.5)

| Script | Output | Role |
|---|---|---|
| `sisso_analysis.py` | `results/sisso_results.csv` | SISSO Full (Eq. 3): best BIC, hidden singularity |
| `sisso_robust.py` | `results/sisso_robust_comparison.csv` | Bounded variant (Eq. 4): deployable, ext RMSE 163 MPa |
| `sisso_analysis_v2.py` | `results/sisso_v2_*.csv` | Expanded-search control (SI §S6) |
| `sisso_with_sdgrain.py` | `results/sisso_sdgrain_results.csv` | SISSO with SD_grain in the pool — selects d^-1/2·SD_grain |
| `pysr_grid_analysis.py` (+ `run_pysr_grid_subprocess.sh`, `recompute_pysr_grid_loo.py`) | `results/pysr_grid_summary_*.csv`, `results/pysr_grid/` | F1–F3 × O1–O3 grid, elbow + accuracy selections |
| `pysr_analysis.py`, `pysr_outer_loop_cv.py` | Pareto fronts, outer-loop CV | PySR baseline + expensive outer-loop control |
| `eml_regression.py` | `results/eml_results.csv` | Universal-operator SR control (SI §S6) |
| `hardness_symbolic_regression.py` | `results/hardness_sr_results.csv` | HV elbow equation under refit LOO + LOBO (Eq. 5) |
| `s5_symbolic_comparison.py` | `results/s5_symbolic_comparison.csv` | PySR vs SISSO matched on identical curated-Wen inputs |
