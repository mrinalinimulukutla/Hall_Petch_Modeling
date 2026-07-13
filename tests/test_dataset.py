"""Dataset structure regression checks.

These tests pin down the basic shape of the data so that an accidental
filter, dropna, or extra row in the upstream xlsx fails CI rather than
silently changing every downstream number.
"""


def test_total_row_count(df_ys, df_hv):
    """94 alloys total; 93 with YS, 94 with HV, 93 with both."""
    # df_ys is dropna(YS) -> 93 rows
    assert len(df_ys) == 93, f"Expected 93 alloys with YS, got {len(df_ys)}"
    assert len(df_hv) == 94, f"Expected 94 alloys with HV, got {len(df_hv)}"


def test_both_ys_and_hv_count(df_both):
    """93 alloys have both YS and HV measurements."""
    assert len(df_both) == 93


def test_per_batch_counts_ys(df_ys):
    """Per-batch composition of the 93-alloy YS dataset."""
    counts = df_ys['Iteration'].value_counts().to_dict()
    expected = {'BBA': 17, 'BBB': 9, 'BBC': 8, 'CBA': 23, 'CBB': 15, 'CBC': 21}
    assert counts == expected, f"Per-batch counts changed: {counts}"


def test_per_batch_counts_hv(df_hv):
    """Per-batch composition of the 94-alloy HV dataset (one extra in BBA)."""
    counts = df_hv['Iteration'].value_counts().to_dict()
    expected = {'BBA': 18, 'BBB': 9, 'BBC': 8, 'CBA': 23, 'CBB': 15, 'CBC': 21}
    assert counts == expected


def test_ys_range(df_ys):
    """YS spans 152-544 MPa as reported in the paper."""
    assert 151 < df_ys['YS'].min() < 153
    assert 543 < df_ys['YS'].max() < 545


def test_grain_size_range(df_ys):
    """Grain size spans 15-212 um as reported in the paper."""
    assert 14 < df_ys['GrainSize'].min() < 16
    assert 211 < df_ys['GrainSize'].max() < 213


def test_b_campaign_processing_is_uniform(df_ys):
    """All B-campaign alloys share CW=60, RecrystT=950 (Section 5.7 claim)."""
    b = df_ys[df_ys['Iteration'].str.startswith('B')]
    assert b['ColdWork'].nunique() == 1
    assert b['RecrystT'].nunique() == 1
    assert b['ColdWork'].iloc[0] == 60
    assert b['RecrystT'].iloc[0] == 950


def test_c_campaign_recrystt_spans_decade(df_ys):
    """C-campaign sweeps RecrystT 675-1250 C (Section 5.7 claim)."""
    c = df_ys[df_ys['Iteration'].str.startswith('C')]
    assert c['RecrystT'].min() < 700
    assert c['RecrystT'].max() > 1200
