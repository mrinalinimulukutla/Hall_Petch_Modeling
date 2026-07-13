"""M3 composition-dependent Hall-Petch regression checks (paper §4.6).

M3 fits sigma_y = sigma_00 + sum_i alpha_i * x_i + k_HP * d^(-1/2)
using all 7 non-Ni element fractions as composition descriptors.

These tests re-fit M3 from data (fast: ~1s, no ML). They verify the
headline coefficients (alpha_V = +291 MPa, k_HP = 766 MPa·um^(1/2))
and the LOO R^2 = 0.652.
"""
import numpy as np
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import LeaveOneOut

# Ni is the solvent and absorbed into the intercept; the other 7 elements
# enter the composition descriptor vector.
NON_NI_ELEMENTS = ['Al', 'Co', 'Cr', 'Cu', 'Fe', 'Mn', 'V']


@pytest.fixture(scope='module')
def m3_fit(df_ys):
    """Refit M3 from data and return (model, predictions, LOO predictions)."""
    X = np.column_stack(
        [df_ys[f'{el}_frac'].values for el in NON_NI_ELEMENTS]
        + [df_ys['d_inv_sqrt'].values]
    )
    y = df_ys['YS'].values
    m = LinearRegression().fit(X, y)

    # LOO predictions via leave-one-out
    preds_loo = np.zeros_like(y, dtype=float)
    for tr, te in LeaveOneOut().split(X):
        mi = LinearRegression().fit(X[tr], y[tr])
        preds_loo[te] = mi.predict(X[te])

    return {
        'model': m,
        'r2_train': m.score(X, y),
        'r2_loo': r2_score(y, preds_loo),
        'alphas': dict(zip(NON_NI_ELEMENTS, m.coef_[:7])),
        'k_HP': m.coef_[7],
        'intercept': m.intercept_,
    }


def test_m3_loo_r2(m3_fit):
    """M3 LOO R^2 = 0.652 (paper §4.6)."""
    assert np.isclose(m3_fit['r2_loo'], 0.652, atol=0.005), \
        f"M3 LOO R^2 = {m3_fit['r2_loo']:.4f}, expected 0.652"


def test_m3_alpha_V_is_largest_positive(m3_fit):
    """alpha_V = +291 MPa (paper §4.6, the largest positive coefficient)."""
    assert np.isclose(m3_fit['alphas']['V'], 291, atol=10), \
        f"alpha_V = {m3_fit['alphas']['V']:.1f}, expected 291"

    # And it must be the largest positive among all 7 alpha_i
    positives = {el: a for el, a in m3_fit['alphas'].items() if a > 0}
    assert max(positives, key=positives.get) == 'V', \
        "V should be the element with the largest positive M3 coefficient"


def test_m3_k_HP(m3_fit):
    """k_HP = 766 MPa·um^(1/2) (paper §4.6, Table 9 'This work' row)."""
    assert np.isclose(m3_fit['k_HP'], 766, atol=10), \
        f"k_HP = {m3_fit['k_HP']:.1f}, expected 766"


def test_m3_k_HP_within_literature_range(m3_fit):
    """k_HP should fall within the 494-1014 MPa·um^(1/2) FCC HEA literature range (paper Table 9)."""
    assert 400 < m3_fit['k_HP'] < 1100, \
        f"k_HP = {m3_fit['k_HP']:.1f} outside plausible FCC HEA range"


def test_m3_improves_over_baseline(df_ys, m3_fit):
    """M3 LOO R^2 must beat baseline Hall-Petch LOO R^2 = 0.406."""
    # Refit baseline HP (just d^(-1/2))
    y = df_ys['YS'].values
    X_hp = df_ys['d_inv_sqrt'].values.reshape(-1, 1)
    preds_loo = np.zeros_like(y, dtype=float)
    for tr, te in LeaveOneOut().split(X_hp):
        mi = LinearRegression().fit(X_hp[tr], y[tr])
        preds_loo[te] = mi.predict(X_hp[te])
    r2_hp = r2_score(y, preds_loo)
    assert np.isclose(r2_hp, 0.406, atol=0.01), \
        f"Baseline HP LOO R^2 = {r2_hp:.4f}, expected 0.406"
    assert m3_fit['r2_loo'] > r2_hp + 0.1, \
        "M3 should beat baseline HP by at least 0.1 in LOO R^2"
