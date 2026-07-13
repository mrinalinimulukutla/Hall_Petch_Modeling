"""Regression tests on the joblib-pickled fitted models.

scripts/export_fitted_models.py writes:
  results/m3_model.pkl                  Fitted M3 sklearn LinearRegression
  results/m3_coefficients.csv           Human-readable coefficient table
  results/hv_baseline_model.pkl         Fitted HV Hall-Petch sklearn model
  results/hv_baseline_coefficients.csv  Human-readable parameter table

These tests load the pickles and assert the paper's headline values.
They protect against drift between the committed pickles and what the
exporter would produce from current data -- if anyone updates the data
without regenerating the pickles, CI fails here.

Run `make export-models` to refresh the pickles from current data.
"""
import numpy as np
import pandas as pd
import pytest
from joblib import load


@pytest.fixture(scope='module')
def m3():
    from _config import RESULTS_DIR
    return load(RESULTS_DIR / 'm3_model.pkl')


@pytest.fixture(scope='module')
def m3_coefs():
    from _config import RESULTS_DIR
    return pd.read_csv(RESULTS_DIR / 'm3_coefficients.csv').set_index('coefficient')


@pytest.fixture(scope='module')
def hv_baseline():
    from _config import RESULTS_DIR
    return load(RESULTS_DIR / 'hv_baseline_model.pkl')


@pytest.fixture(scope='module')
def hv_coefs():
    from _config import RESULTS_DIR
    return pd.read_csv(RESULTS_DIR / 'hv_baseline_coefficients.csv').set_index('parameter')


# --- M3 (sklearn LinearRegression with 8 coefs + intercept) ---

def test_m3_intercept(m3):
    """sigma_00 ≈ 230 MPa (Ni-solvent baseline)."""
    assert np.isclose(m3.intercept_, 230, atol=10), \
        f"M3 intercept = {m3.intercept_:.1f}, expected ~230"


def test_m3_alpha_V(m3):
    """alpha_V = +291 MPa (paper Table 8; largest positive coefficient)."""
    # m3.coef_ order: [Al, Co, Cr, Cu, Fe, Mn, V, k_HP]
    alpha_V = m3.coef_[6]
    assert np.isclose(alpha_V, 291, atol=10), \
        f"alpha_V = {alpha_V:.1f}, expected 291"


def test_m3_alpha_Fe_negative(m3):
    """alpha_Fe ≈ -360 MPa (largest-magnitude negative coefficient)."""
    alpha_Fe = m3.coef_[4]
    assert np.isclose(alpha_Fe, -360, atol=10), \
        f"alpha_Fe = {alpha_Fe:.1f}, expected -360"


def test_m3_k_HP(m3):
    """k_HP = 766 MPa.um^(1/2) (paper §4.6)."""
    k_HP = m3.coef_[7]
    assert np.isclose(k_HP, 766, atol=10), \
        f"k_HP = {k_HP:.1f}, expected 766"


def test_m3_csv_matches_pickle(m3, m3_coefs):
    """The CSV table and the pickled model must report the same numbers."""
    assert np.isclose(m3_coefs.loc['intercept (sigma_00)', 'value'], m3.intercept_)
    assert np.isclose(m3_coefs.loc['alpha_V', 'value'], m3.coef_[6])
    assert np.isclose(m3_coefs.loc['k_HP', 'value'], m3.coef_[7])


def test_m3_pickled_R2_LOO(m3_coefs):
    """LOO R^2 = 0.652 from the exported coefficient table."""
    r2 = m3_coefs.loc['R2_LOO', 'value']
    assert np.isclose(r2, 0.652, atol=0.005), \
        f"M3 LOO R^2 (from CSV) = {r2:.4f}, expected 0.652"


def test_m3_predict_from_pickle(m3):
    """The pickled model must predict correctly on a known input.

    Pure-Ni alloy at d = 100 um: sigma_y = sigma_00 + k_HP * 100^(-1/2)
                                       = 230 + 766 / 10 = 306.6 MPa.
    """
    # All-zero composition (pure Ni after the intercept absorbs it)
    x = np.array([[0, 0, 0, 0, 0, 0, 0, 100**(-0.5)]])
    pred = m3.predict(x)[0]
    # Expected: intercept + k_HP * d^(-1/2)
    expected = m3.intercept_ + m3.coef_[7] * 100**(-0.5)
    assert np.isclose(pred, expected, atol=0.01)
    # Sanity check on the magnitude
    assert 250 < pred < 350


# --- HV Hall-Petch baseline ---

def test_hv_baseline_H0(hv_baseline, hv_coefs):
    """H_0 = 86.7 HV (paper §4.11)."""
    assert np.isclose(hv_baseline.intercept_, 86.7, atol=1.0), \
        f"H_0 = {hv_baseline.intercept_:.1f}, expected 86.7"
    assert np.isclose(hv_coefs.loc['H_0', 'value'], 86.7, atol=1.0)


def test_hv_baseline_kH(hv_baseline, hv_coefs):
    """k_H = 306 HV.um^(1/2) (paper §4.11)."""
    assert np.isclose(hv_baseline.coef_[0], 306, atol=5), \
        f"k_H = {hv_baseline.coef_[0]:.1f}, expected 306"
    assert np.isclose(hv_coefs.loc['k_H', 'value'], 306, atol=5)


def test_hv_baseline_optimized_exponent(hv_coefs):
    """Optimized HV grain-size exponent n = 1.73 (paper §4.11)."""
    n_opt = hv_coefs.loc['n_optimized', 'value']
    assert np.isclose(n_opt, 1.73, atol=0.02), \
        f"HV optimized exponent = {n_opt:.3f}, expected 1.73"


def test_hv_baseline_R2_LOO(hv_coefs):
    """HV Hall-Petch LOO R^2 = 0.136 (paper §4.11; weak)."""
    r2 = hv_coefs.loc['R2_LOO', 'value']
    assert np.isclose(r2, 0.136, atol=0.005), \
        f"HV HP LOO R^2 = {r2:.4f}, expected 0.136"
