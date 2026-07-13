"""Shared pytest fixtures and path setup.

Adds the scripts/ directory to sys.path so tests can import _config
and call into the analysis modules without re-implementing path discovery.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

import pytest


@pytest.fixture(scope='session')
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope='session')
def df_ys():
    """The 93-alloy YS dataset with descriptors."""
    import pandas as pd
    from _config import DATA_DIR
    df = pd.read_csv(DATA_DIR / 'data_with_descriptors.csv')
    return df.dropna(subset=['YS']).reset_index(drop=True)


@pytest.fixture(scope='session')
def df_hv():
    """The 94-alloy HV dataset (includes the 1 alloy without YS)."""
    import pandas as pd
    from _config import DATA_DIR
    df = pd.read_csv(DATA_DIR / 'data_with_descriptors.csv')
    return df.dropna(subset=['HV']).reset_index(drop=True)


@pytest.fixture(scope='session')
def df_both():
    """The 93-alloy subset with both YS and HV measurements."""
    import pandas as pd
    from _config import DATA_DIR
    df = pd.read_csv(DATA_DIR / 'data_with_descriptors.csv')
    return df.dropna(subset=['HV', 'YS']).reset_index(drop=True)
