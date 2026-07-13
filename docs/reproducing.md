# Reproducing the analysis

Everything regenerable in this repository is driven by the `Makefile`; run
`make help` for the annotated target list. This page gives the canonical
stage order for a full end-to-end reproduction from raw data (~85 min on a
laptop, excluding the optional expensive controls), and what each stage must
produce before the next one starts.

All scripts read paths from `scripts/_config.py` — nothing depends on the
current working directory, and cloning the repo anywhere works unchanged.

## Environment

```bash
make install          # pip install -r requirements.txt
make test             # verify the pre-computed state before touching anything
```

Notes on optional dependencies: `make bayesian` needs PyMC + ArviZ;
`make pysr` needs Julia (PySR installs it on first run); `make sisso` uses
TorchSISSO (pure Python, no Julia). All other stages run on the core
scientific stack.

## Stage order

| # | Stage | Command | Time | Key outputs |
|---|-------|---------|------|-------------|
| 0 | Descriptors + feature ladder | `make data` | ~1 min | `data/derived/{data_with_descriptors,data_with_vlc,inputs}.csv` |
| 0b | Pre-modeling diagnostics | `make diagnostics` | ~1 min | hull overlap, noise ceiling, within-replicate k_HP |
| 1 | Grain-size scaling laws | `make scaling` | ~5 min | scaling-law comparison CSVs |
| 1b | Bayesian scaling comparison | `make bayesian` | ~10 min | `bayesian_model_comparison.csv` |
| 2 | SSS audit | `make sss pca-ols` | ~3 min | SSS benchmark + PCA-OLS CSVs |
| 3 | Composition-HP hierarchy | `make comp-hp export-models` | ~5 min | `comp_hp_model_comparison.csv`, M15 comparison, model pickles |
| 4 | Non-linear ML | `make ml fair` | ~35 min | 17-model panel, fair-comparison CSVs |
| 5 | Symbolic regression | `make symbolic` | ~25 min | SISSO/PySR/EML results, HV elbow refit |
| 6 | Validation floor | `make cv-comparison external audit bootstrap-sr per-batch-lobo mc-grain vif ceiling` | ~5 min | external RMSEs, singularity audit, bootstrap CIs |
| 7 | Hardness/Tabor | `make hardness` | ~2 min | C_eff, HV scaling, rank analysis |
| 8 | Unified table | `make unified` | ~10 s | `unified_model_table.csv` |
| 9 | Figures | `make figures` | ~2 min | `paper/figures/`, `analysis_plots/` |
| 10 | Documents | `make all` | ~5 min | paper PDFs, notebook, report |

After any stage, `make test` re-asserts the canonical values (CLAUDE.md §3);
a failing test after a re-run means the environment, not the code, changed —
investigate before editing anything downstream.

## Expensive optional controls

- `make armote-ladder` — ARMOTE S1–S4 summary from the shared ladder
  (the full nested-CV ARMOTE panel with per-fold Optuna studies is archived
  separately, ~1.5 GB).
- `scripts/05_tier5_symbolic_regression/pysr_outer_loop_cv.py` — outer-loop
  PySR CV, ~30 min per fold.

## Determinism

Fixed seeds are set inside each script. PySR is evolutionary and can return
different (equally scoring) expressions across runs; the elbow/accuracy
selections and their cross-validated metrics are what the regression tests
lock, not the expression strings. SISSO reruns are deterministic.
