"""External validation regression checks (paper §4.10).

SISSO Full fails catastrophically on the external set (RMSE = 421 MPa)
because of the delta_mu singularity. SISSO Robust achieves RMSE = 163 MPa
on 82 independent literature data points. M3 achieves RMSE = 133 MPa.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope='module')
def ext():
    """External validation results CSV."""
    from _config import RESULTS_DIR
    return pd.read_csv(RESULTS_DIR / 'external_validation_results.csv')


def test_external_set_size(ext):
    """82 external data points (paper §4.10)."""
    assert len(ext) == 82, f"External set has {len(ext)} points, expected 82"


def test_sisso_full_external_rmse_catastrophic(ext):
    """SISSO Full RMSE = 421 MPa on external set (paper §4.10)."""
    rmse = np.sqrt(np.mean(ext['residual_SISSO'].values ** 2))
    assert np.isclose(rmse, 421, atol=10), f"SISSO Full external RMSE = {rmse:.1f}, expected 421"


def test_sisso_robust_external_rmse(ext):
    """SISSO Robust RMSE = 163 MPa on external set (paper §4.10).

    Was 122 MPa in earlier drafts before the canonical rerun.
    """
    rmse = np.sqrt(np.mean(ext['residual_SISSO_robust'].values ** 2))
    assert np.isclose(rmse, 163, atol=10), f"SISSO Robust external RMSE = {rmse:.1f}, expected 163"


def test_m3_external_rmse(ext):
    """M3 RMSE = 133 MPa on external set (paper §4.10, best for external)."""
    rmse = np.sqrt(np.mean(ext['residual_M3'].values ** 2))
    assert np.isclose(rmse, 133, atol=10), f"M3 external RMSE = {rmse:.1f}, expected 133"


def test_robust_beats_full_on_external(ext):
    """SISSO Robust must outperform SISSO Full on external data (Eq. 5 motivation)."""
    rmse_full = np.sqrt(np.mean(ext['residual_SISSO'].values ** 2))
    rmse_robust = np.sqrt(np.mean(ext['residual_SISSO_robust'].values ** 2))
    assert rmse_robust < rmse_full / 2, \
        "SISSO Robust should beat Full by at least 2x on external (paper claim)"
