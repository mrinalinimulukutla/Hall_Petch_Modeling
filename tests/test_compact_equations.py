"""Regression tests on the compact-equation stream published symbolic equations.

These tests lock the *symbolic form* of the published equations. When the
fitted constants migrate to a new repo and are refit, the form must not
change — only the numeric values. This guards against silent equation
drift between the conference deck and the paper.

Numeric tests on the constants come later, once the integration pipeline
has fit them under LOO + LOBO and they are accepted as canonical.
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))


def test_hv_elbow_form_in_hardness_sr():
    """HV elbow equation: 221.46 - 83.95*(6.93-d)/SD + dH_mix/t^2"""
    src = next((REPO_ROOT / 'scripts').rglob('hardness_symbolic_regression.py')).read_text()
    assert '221.46' in src
    assert '83.95' in src
    assert '6.93' in src
    assert 'SD_GS' in src or 'SD_grain' in src or 'GrainSize_SD' in src or 'GS_SD' in src
    assert 'dH_mix' in src or 'dH ' in src
    assert 't_hold' in src or 'HoldTime' in src


def test_ys_compact_form_in_bootstrap():
    """YS compact: VEC * (4.29 * dH * SD / (d^2 * dchi) - 2.13/dchi + 56.06)"""
    src = next((REPO_ROOT / 'scripts').rglob('bootstrap_sr_constants.py')).read_text()
    assert '4.29' in src
    assert '2.13' in src
    assert '56.06' in src
    assert 'VEC' in src
    assert 'delta_chi' in src or 'dchi' in src


def test_singularity_audit_covers_all_published_equations():
    """singularity_audit.py must reference all four canonical equations."""
    src = next((REPO_ROOT / 'scripts').rglob('singularity_audit.py')).read_text()
    for name in (
        'Compact_YS_equation',
        'Compact_HV_elbow',
        'SISSO_Full',
        'SISSO_Robust',
    ):
        assert name in src, f"singularity_audit.py must include {name}"


def test_compact_ys_constants_match_canonical():
    """The compact YS equation's *default* constants in the codebase must
    match the published canonical values. If you refit under the
    integration protocol and get new numbers, update this test in the same
    commit so the change is auditable."""
    src = next((REPO_ROOT / 'scripts').rglob('bootstrap_sr_constants.py')).read_text()
    # conference deck: c1=4.29, c2=-2.13, c3=56.06
    assert re.search(r'p0=\[4\.29,\s*-?2\.13,\s*56\.06\]', src), (
        "Compact YS p0 must be [4.29, -2.13, 56.06] (conference deck values).")
