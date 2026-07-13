"""SISSO canonical-number regression checks.

These tests read from results/sisso_results.csv and results/sisso_robust_comparison.csv
(committed canonical CSVs from the deterministic SISSO run, May 2026).

They do NOT re-run SISSO (which takes ~1 minute and requires torch-sisso).
They protect against accidental edits to the CSVs, against silent path
drift after the May 2026 reorg, and against future SISSO reruns that
would produce different numbers without updating the paper.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope='module')
def sisso_full():
    """The SISSO Full (Eq. 4 in the paper) result row."""
    from _config import RESULTS_DIR
    df = pd.read_csv(RESULTS_DIR / 'sisso_results.csv')
    return df[df['Model'] == 'SISSO Full'].iloc[0]


@pytest.fixture(scope='module')
def sisso_robust():
    """The SISSO Robust (Eq. 5 in the paper) result row."""
    from _config import RESULTS_DIR
    df = pd.read_csv(RESULTS_DIR / 'sisso_robust_comparison.csv')
    return df[df['variant'] == 'no_delta_mu'].iloc[0]


# --- SISSO Full (Eq. 4) ---

def test_sisso_full_loo_r2(sisso_full):
    """LOO R^2 = 0.665 (paper Table 15, §4.8). Was 0.671 in earlier drafts."""
    assert np.isclose(sisso_full['LOO_R2'], 0.665, atol=0.005), \
        f"SISSO Full LOO R^2 = {sisso_full['LOO_R2']:.4f}, expected 0.665"


def test_sisso_full_rmse(sisso_full):
    """RMSE = 46.9 MPa (paper §4.8). Was 46.5 in earlier drafts."""
    assert np.isclose(sisso_full['LOO_RMSE'], 46.9, atol=0.2), \
        f"SISSO Full RMSE = {sisso_full['LOO_RMSE']:.2f}, expected 46.9"


def test_sisso_full_lobo_r2(sisso_full):
    """LOBO R^2 = 0.380 (paper §4.8). Was 0.492 in earlier drafts."""
    assert np.isclose(sisso_full['LOBO_R2'], 0.380, atol=0.005), \
        f"SISSO Full LOBO R^2 = {sisso_full['LOBO_R2']:.4f}, expected 0.380"


def test_sisso_full_bic(sisso_full):
    """BIC = 714 (best BIC among all 23 models; paper Table 15)."""
    assert np.isclose(sisso_full['BIC'], 714, atol=1), \
        f"SISSO Full BIC = {sisso_full['BIC']:.1f}, expected 714"


def test_sisso_full_n_parameters(sisso_full):
    """4 effective parameters: 3 term coefficients + 1 intercept."""
    assert sisso_full['k_eff'] == 4


# --- SISSO Robust (Eq. 5) ---

def test_sisso_robust_loo_r2(sisso_robust):
    """LOO R^2 = 0.609 (paper §4.8). Was 0.626 in earlier drafts."""
    assert np.isclose(sisso_robust['loo_r2'], 0.609, atol=0.005), \
        f"SISSO Robust LOO R^2 = {sisso_robust['loo_r2']:.4f}, expected 0.609"


def test_sisso_robust_rmse(sisso_robust):
    """RMSE = 50.7 MPa (paper §4.8). Was 49.6 in earlier drafts."""
    assert np.isclose(sisso_robust['loo_rmse'], 50.7, atol=0.2), \
        f"SISSO Robust RMSE = {sisso_robust['loo_rmse']:.2f}, expected 50.7"


def test_sisso_robust_bic(sisso_robust):
    """BIC = 717 (paper Table 15)."""
    assert np.isclose(sisso_robust['bic'], 717, atol=1), \
        f"SISSO Robust BIC = {sisso_robust['bic']:.1f}, expected 717"


def test_sisso_robust_no_singularity(sisso_robust):
    """The robust variant must have 0 unphysical predictions (vs 1 for SISSO Full)."""
    assert sisso_robust['n_unphysical'] == 0, \
        "SISSO Robust must avoid the delta_mu singularity"


# --- Cross-check ΔR^2 between Full and Robust ---

def test_delta_r2_full_vs_robust(sisso_full, sisso_robust):
    """ΔR^2_LOO = 0.665 − 0.609 = 0.056 (paper §4.8, §5.4)."""
    delta = sisso_full['LOO_R2'] - sisso_robust['loo_r2']
    assert np.isclose(delta, 0.056, atol=0.005), \
        f"ΔR^2_LOO = {delta:.4f}, expected 0.056"
