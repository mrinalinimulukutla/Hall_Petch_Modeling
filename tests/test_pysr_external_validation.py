"""PySR external-validation + BIC regression checks.

These tests read results/pysr_external_validation.csv (produced by
scripts/pysr_external_validation.py), which scores every PySR grid equation
with the SAME BIC formula and the SAME 82-point external dataset that SISSO
used — closing the gap where PySR rows were BIC = TBD / Ext_RMSE = TBD.

They protect three things:
  1. Every PySR equation has a finite BIC and an external-set score.
  2. The HV equations that blow up on external data (predictions far outside
     the physical hardness range) are flagged Singularity_safe = no — the
     same deployment failure mode SISSO Full exhibits.
  3. At least one singularity-safe PySR-YS equation beats SISSO Full's
     external RMSE (420.6 MPa) on the same set.
"""
import numpy as np
import pandas as pd
import pytest


@pytest.fixture(scope='module')
def pysr_ext():
    from _config import RESULTS_DIR
    return pd.read_csv(RESULTS_DIR / 'pysr_external_validation.csv')


def test_all_equations_scored(pysr_ext):
    """36 equations (18 YS + 18 HV), each with a finite BIC."""
    assert len(pysr_ext) == 36, f"expected 36 scored equations, got {len(pysr_ext)}"
    assert pysr_ext['BIC'].notna().all(), "every PySR equation must have a BIC"
    assert {'YS', 'HV'} == set(pysr_ext['Target'].unique())


def test_no_tbd_remaining(pysr_ext):
    """The whole point: no Singularity_safe = TBD left."""
    assert (pysr_ext['Singularity_safe'] == 'TBD').sum() == 0


def test_hv_blowups_flagged_unsafe(pysr_ext):
    """HV equations with division operators blow up externally (preds far
    above the physical HV range) and must be flagged unsafe."""
    blown = pysr_ext[(pysr_ext['Target'] == 'HV')
                     & (pd.to_numeric(pysr_ext['Ext_RMSE_MPa'], errors='coerce') > 1000)]
    assert len(blown) >= 1, "expected at least one HV singularity blow-up"
    assert (blown['Singularity_safe'] == 'no').all(), \
        "HV equations with >1000 external RMSE must be Singularity_safe = no"


def test_best_safe_ys_beats_sisso_full(pysr_ext):
    """A singularity-safe PySR-YS equation should beat SISSO Full's external
    RMSE of 420.6 MPa on the same 82-point set."""
    ys_safe = pysr_ext[(pysr_ext['Target'] == 'YS')
                       & (pysr_ext['Singularity_safe'] == 'yes')].copy()
    ys_safe['Ext_RMSE_MPa'] = pd.to_numeric(ys_safe['Ext_RMSE_MPa'], errors='coerce')
    best = ys_safe['Ext_RMSE_MPa'].min()
    assert best < 420.6, f"best safe PySR-YS external RMSE = {best:.1f}, expected < 420.6"


def test_external_set_size(pysr_ext):
    """YS scored on the full 82-point set; HV on the 25 Huang HV points."""
    ys = pysr_ext[pysr_ext['Target'] == 'YS']['n_ext'].unique()
    hv = pysr_ext[pysr_ext['Target'] == 'HV']['n_ext'].unique()
    assert list(ys) == [82], f"YS external n should be 82, got {ys}"
    assert list(hv) == [25], f"HV external n should be 25, got {hv}"
