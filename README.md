# Physics-Informed ML for Hall–Petch Strengthening in FCC High-Entropy Alloys

Companion repository for the manuscript *"Revisiting Hall–Petch strengthening
in FCC high-entropy alloys: Best practices for building and auditing
machine-learning strength models"* (Acta Materialia, in preparation).

We model yield strength (YS) and Vickers hardness (HV) of 94 FCC high-entropy
alloys in the Al–Co–Cr–Cu–Fe–Mn–Ni–V system and develop a best-practices
framework in which ML both **constructs** predictive models and **audits**
physics-informed ones. The analysis is a controlled ascent in model
flexibility — the "staircase" — with every tier validated under 5-fold,
leave-one-out (LOO), leave-one-batch-out (LOBO), and external validation,
plus a singularity audit of every closed-form equation.

```
Tier 1  grain size only          (classical + alternative Hall–Petch laws)
Tier 2  + SSS physics descriptors (VLC, Labusch, Toda-Caraballo; Wen; PCA)
Tier 3  + composition/processing  (linear M-model hierarchy, M0–M15)
Tier 4  + non-linear ML           (equal-footing panel; ARMOTE-CV)
Tier 5  → symbolic regression     (PySR, SISSO; discovery + deployment audit)
        ─ validation floor ─      (5-fold · LOO · LOBO · external · singularity)
```

## Quick start

```bash
git clone <repo-url> Physics_informed_ML_Hall_Petch
cd Physics_informed_ML_Hall_Petch
make install                 # pip install -r requirements.txt
make help                    # list every Makefile target with one-liners
make test                    # run the regression test suite (~30 s)
make paper                   # build paper/main.pdf + supplementary.pdf
jupyter notebook notebook/Hall_Petch_HEA_Analysis.ipynb
```

The notebook loads pre-computed CSVs from `results/` and renders all figures
in a few minutes. To regenerate a specific result, use the matching Makefile
stage (e.g., `make sisso`, `make hardness`, `make external`). For a full
end-to-end reproduction from raw data, follow `docs/reproducing.md` (~85 min).

## Repository layout

```
Physics_informed_ML_Hall_Petch/
├── data/
│   ├── raw/                       Grain_Size_Summary_v3.xlsx (the only true input)
│   └── derived/                   Computed descriptors + the shared S1–S4
│                                  feature ladder (inputs.csv + manifest)
├── scripts/                       Analysis scripts, organized by tier
│   ├── _config.py                 Shared paths; makes all tier folders importable
│   ├── 00_data_preparation/       EDA, descriptors, VLC inputs, feature ladder
│   ├── 01_tier1_grain_size/       Nine scaling laws, Bayesian PSIS-LOO comparison
│   ├── 02_tier2_sss_descriptors/  VLC/Labusch/Toda-Caraballo audit; PCA-OLS
│   ├── 03_tier3_composition_hp/   M-model hierarchy incl. SD_grain (M13/M15)
│   ├── 04_tier4_nonlinear_ml/     17-model panel, SHAP, equal-footing fair comparison
│   ├── 05_tier5_symbolic_regression/  PySR grid, SISSO Full/Robust/+SD, EML
│   ├── 06_validation_floor/       LOO/LOBO/external validation, singularity audit,
│   │                              bootstrap CIs, unified model table
│   ├── 07_hardness_tabor/         Tabor C_eff, HV–YS rank (Simpson's paradox)
│   └── figures/                   Publication-figure generation
├── results/                       Output CSVs (+ fitted-model pickles), regenerable
├── analysis_plots/                Generated PNG figures (numbered NN_description.png)
├── notebook/                      _generate_notebook.py (source of truth) +
│                                  Hall_Petch_HEA_Analysis.ipynb (generated)
├── paper/                         LaTeX: main.tex, supplementary.tex,
│                                  references.bib, figures/
├── report/                        generate_report.py → Comprehensive_Analysis_Report.docx
├── docs/                          reproducing.md, literature_review.md
├── tests/                         Regression tests locking canonical values
├── Makefile · requirements.txt · CITATION.cff · .zenodo.json · LICENSE (MIT)
```

Each `scripts/` subfolder has its own README mapping every script to its
inputs, outputs, and the paper section it supports.

## Reproducing key results

| Result (paper section) | Command | Runtime |
|---|---|---|
| Descriptors + feature ladder (§2) | `make data` | ~1 min |
| Scaling laws, frequentist + Bayesian (§4.1) | `make scaling bayesian` | ~15 min |
| SSS audit + redundancy (§4.2) | `make sss` | ~2 min |
| M-model hierarchy incl. M15 (§4.3) | `make comp-hp` | ~5 min |
| Non-linear panel + fair comparison (§4.4) | `make ml fair` | ~35 min |
| PySR grid + SISSO variants (§4.5) | `make symbolic` | ~25 min |
| External validation + singularity audit (§4.5) | `make external audit` | ~3 min |
| Tabor + HV–YS ranking (§4.7) | `make hardness` | ~2 min |
| Unified model table (§4.8) | `make unified` | ~10 s |
| All paper figures | `make figures` | ~2 min |

Every cross-validated number in the paper reports LOO **and** LOBO; the
unified comparison lives in `results/unified_model_table.csv`.

## Verifying headline coefficients without re-running anything

```python
from joblib import load
m3 = load('results/m3_model.pkl')
print(dict(zip(['Al','Co','Cr','Cu','Fe','Mn','V','k_HP'], m3.coef_)))
# → {'V': 291.27, 'k_HP': 765.76, ...}
```

`results/m3_coefficients.csv` and `results/hv_baseline_coefficients.csv`
carry OLS standard errors and 95 % confidence intervals for every parameter.

## Data

`data/raw/Grain_Size_Summary_v3.xlsx` contains composition, processing
parameters, grain size, within-alloy grain-size standard deviation
(SD_grain), yield strength, and Vickers hardness for the 94 alloys
(93 with YS), produced in two Bayesian-optimization campaigns under the
BIRDSHOT initiative (ARL HTMDEC program). External-validation literature
data (82 points, four sources) are in
`results/external_validation_results.csv`.

## Related repositories

The nested-CV non-linear panel (ARMOTE-CV: 8 regressors × S1–S4 ladder ×
three CV protocols, with per-fold Optuna studies and model pickles, ~1.5 GB)
is archived separately; its summary metrics are included here as
`results/armote_ladder_cv.csv`. Cited-literature PDFs are not redistributed;
all references are in `paper/references.bib`.

## Citing

If you use this code or data, please cite the manuscript (see
`CITATION.cff`) and the Zenodo archive:
`https://doi.org/10.5281/zenodo.XXXXXXX` (minted on first release).

## License

MIT — see `LICENSE`.
