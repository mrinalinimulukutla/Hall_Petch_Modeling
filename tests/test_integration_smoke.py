"""Smoke tests for the compact-equation stream scripts.

These tests only verify that:
  - Each integration script imports without error.
  - The _config path constants resolve to existing folders.
  - The expected output CSV file path is well-formed.

Deep regression tests (locking canonical numbers) come in separate
test_<feature>.py files once each script has produced its first stable
output.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / 'scripts'

INTEGRATION_SCRIPTS = [
    'pca_ols_analysis',
    'pysr_grid_analysis',
    'hardness_symbolic_regression',
    'singularity_audit',
    'variance_ceiling',
    'unified_model_table',
    'bootstrap_sr_constants',
    'vif_diagnostics',
    'per_batch_lobo',
    'mc_grain_size_sensitivity',
    'literature_kHP_table',
    'pysr_outer_loop_cv',
]


def test_config_paths_exist():
    """_config.py must expose paths that resolve to existing folders."""
    sys.path.insert(0, str(SCRIPTS))
    from _config import (REPO_ROOT as R, DATA_DIR, RESULTS_DIR, PLOTS_DIR,
                         NOTEBOOK_DIR, PAPER_DIR, REPORT_DIR, DOCS_DIR)
    for p in (R, DATA_DIR.parent, RESULTS_DIR, PLOTS_DIR, NOTEBOOK_DIR,
              PAPER_DIR, REPORT_DIR, DOCS_DIR):
        assert p.exists(), f"{p} does not exist"


@pytest.mark.parametrize('mod_name', INTEGRATION_SCRIPTS)
def test_script_is_syntactically_valid(mod_name):
    """Each integration script must parse — catches Python syntax errors."""
    hits = sorted(SCRIPTS.rglob(f'{mod_name}.py'))
    assert hits, f"{mod_name}.py missing under {SCRIPTS}"
    path = hits[0]
    source = path.read_text()
    compile(source, str(path), 'exec')


def test_unified_table_module_exposes_expected_inputs():
    """unified_model_table.py must enumerate the result CSVs it consumes."""
    src = next(SCRIPTS.rglob('unified_model_table.py')).read_text()
    for required_csv in (
        'pca_ols_results.csv',
        'pysr_grid_summary_YS.csv',
        'hardness_sr_results.csv',
        'sisso_results.csv',
        'external_tier_results.csv',
        'singularity_audit.csv',
    ):
        assert required_csv in src, f"unified_model_table.py must reference {required_csv}"
