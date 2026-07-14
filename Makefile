# Physics_informed_ML_Hall_Petch — staged reproduction
# Run `make help` for the annotated target list. Stage order matches
# docs/reproducing.md and the paper's staircase.

PY      := python
S       := scripts
LATEX   := cd paper && pdflatex -interaction=nonstopmode

.PHONY: help install test clean paper notebook report all \
        data diagnostics scaling bayesian sss pca-ols comp-hp export-models \
        ml fair armote-ladder sisso pysr eml symbolic hardness-sr \
        external audit bootstrap-sr per-batch-lobo mc-grain vif ceiling \
        unified cv-comparison hardness figures

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install:  ## pip install -r requirements.txt
	pip install -r requirements.txt

test:  ## Run regression test suite (~30 s)
	pytest tests/ -q

clean:  ## Remove LaTeX aux files, pytest cache, __pycache__
	rm -f paper/*.aux paper/*.bbl paper/*.blg paper/*.log paper/*.out paper/*.spl paper/*.toc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache

# ---------------- documents ----------------

paper:  ## Build paper/main.pdf + supplementary.pdf (pdflatex x3 + bibtex)
	$(LATEX) main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
	$(LATEX) supplementary.tex && bibtex supplementary && pdflatex -interaction=nonstopmode supplementary.tex && pdflatex -interaction=nonstopmode supplementary.tex
	$(MAKE) clean

notebook:  ## Regenerate the .ipynb from its generator
	$(PY) notebook/_generate_notebook.py

report:  ## Regenerate the Word report (~1 min)
	$(PY) report/generate_report.py

all: notebook paper report  ## Build paper + notebook + report from current results/

# ---------------- stage 0: data ----------------

data:  ## Stage 0: descriptors + VLC + shared feature ladder (inputs.csv)
	$(PY) $(S)/00_data_preparation/eda_analysis.py
	$(PY) $(S)/00_data_preparation/vlc_corrected.py
	$(PY) $(S)/00_data_preparation/build_armote_inputs.py

diagnostics:  ## Stage 0b: pre-modeling diagnostics + within-replicate kHP
	$(PY) $(S)/00_data_preparation/eda_diagnostics.py
	$(PY) $(S)/01_tier1_grain_size/eda_within_replicate_kHP.py

# ---------------- tier 1: grain size ----------------

scaling:  ## Tier 1: Hall-Petch + nine scaling laws (~5 min)
	$(PY) $(S)/01_tier1_grain_size/grain_size_scaling_analysis.py

bayesian:  ## Tier 1b: Bayesian PSIS-LOO scaling comparison (~10 min, PyMC)
	$(PY) $(S)/01_tier1_grain_size/bayesian_scaling_analysis.py

literature-khp:  ## Tier 1c: literature k_HP comparison table
	$(PY) $(S)/01_tier1_grain_size/literature_kHP_table.py

# ---------------- tier 2: SSS descriptors ----------------

sss:  ## Tier 2: VLC + Cantor-anchored Labusch/TC audit
	$(PY) $(S)/02_tier2_sss_descriptors/vlc_sss_analysis.py

pca-ols:  ## Tier 2b: PCA-OLS on curated Wen + SD_grain
	$(PY) $(S)/02_tier2_sss_descriptors/pca_ols_analysis.py

# ---------------- tier 3: composition HP ----------------

comp-hp:  ## Tier 3: M-model hierarchy (M13/M15 table is cached: results/sdgrain_model_comparison.csv)
	$(PY) $(S)/03_tier3_composition_hp/composition_hp_analysis.py
	$(PY) $(S)/03_tier3_composition_hp/kHP_composition_analysis.py

export-models:  ## Tier 3b: refresh fitted-model pickles + coefficient CSVs
	$(PY) $(S)/03_tier3_composition_hp/export_fitted_models.py

# ---------------- tier 4: non-linear ML ----------------

ml:  ## Tier 4: 17-model panel + XGBoost/SHAP (~30 min, Optuna)
	$(PY) $(S)/04_tier4_nonlinear_ml/exhaustive_model_search.py
	$(PY) $(S)/04_tier4_nonlinear_ml/xgboost_shap_analysis.py

fair:  ## Tier 4b: equal-footing fair comparison (zero tuning)
	$(PY) $(S)/04_tier4_nonlinear_ml/fair_comparison.py

armote-ladder:  ## Tier 4c: ARMOTE S1-S4 ladder summary
	$(PY) $(S)/04_tier4_nonlinear_ml/armote_ladder_cv.py

# ---------------- tier 5: symbolic regression ----------------

sisso:  ## Tier 5a: SISSO Full + Robust + v2 + SD_grain (~10 min)
	$(PY) $(S)/05_tier5_symbolic_regression/sisso_analysis.py
	$(PY) $(S)/05_tier5_symbolic_regression/sisso_robust.py
	$(PY) $(S)/05_tier5_symbolic_regression/sisso_analysis_v2.py
	$(PY) $(S)/05_tier5_symbolic_regression/sisso_with_sdgrain.py

pysr:  ## Tier 5b: PySR grid F1-F3 x O1-O3 (~10 min, needs Julia)
	$(PY) $(S)/05_tier5_symbolic_regression/pysr_grid_analysis.py

eml:  ## Tier 5c: EML universal-operator symbolic regression
	$(PY) $(S)/05_tier5_symbolic_regression/eml_regression.py

hardness-sr:  ## Tier 5d: HV elbow equation under refit LOO + LOBO
	$(PY) $(S)/05_tier5_symbolic_regression/hardness_symbolic_regression.py

s5:  ## Tier 5e: PySR vs SISSO matched on identical curated-Wen inputs
	$(PY) $(S)/05_tier5_symbolic_regression/s5_symbolic_comparison.py

symbolic: sisso pysr eml hardness-sr s5  ## All symbolic regression

# ---------------- validation floor ----------------

cv-comparison:  ## 5-fold vs LOO vs LOBO for headline models
	$(PY) $(S)/06_validation_floor/cv_comparison.py

external:  ## External validation on 82 literature points
	$(PY) $(S)/06_validation_floor/external_validation.py
	$(PY) $(S)/06_validation_floor/pysr_external_validation.py

audit:  ## Singularity audit of all compact equations
	$(PY) $(S)/06_validation_floor/singularity_audit.py

bootstrap-sr:  ## Bootstrap CIs on compact-equation constants
	$(PY) $(S)/06_validation_floor/bootstrap_sr_constants.py

per-batch-lobo:  ## Per-batch LOBO breakdown with hull containment
	$(PY) $(S)/06_validation_floor/per_batch_lobo.py

mc-grain:  ## Monte Carlo grain-size sensitivity
	$(PY) $(S)/06_validation_floor/mc_grain_size_sensitivity.py

vif:  ## VIF + condition-number diagnostics
	$(PY) $(S)/06_validation_floor/vif_diagnostics.py

ceiling:  ## Noise-limited R^2 ceiling from variance decomposition
	$(PY) $(S)/06_validation_floor/variance_ceiling.py

unified:  ## Rebuild results/unified_model_table.csv
	$(PY) $(S)/06_validation_floor/unified_model_table.py

# ---------------- hardness / Tabor ----------------

hardness:  ## Tabor C_eff + HV scaling + HV-YS rank analysis
	$(PY) $(S)/07_hardness_tabor/hardness_analysis.py

# ---------------- figures ----------------

figures:  ## Regenerate paper figures from cached CSVs (fast)
	$(PY) $(S)/figures/make_framework_overview.py
	$(PY) $(S)/figures/make_property_figures.py
	$(PY) $(S)/figures/make_provenance_figure.py
	$(PY) $(S)/figures/make_cv_comparison_figure.py
	$(PY) $(S)/figures/make_pysr_sisso_pareto.py
	$(PY) $(S)/figures/replot_fair_comparison_heatmap.py
	$(PY) $(S)/figures/make_graphical_abstract.py
