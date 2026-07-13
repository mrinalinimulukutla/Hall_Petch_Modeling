"""HV-YS rank-correlation regression checks (paper §5.7).

Key claims from the Simpson's-paradox analysis:
- Global Spearman rho ≈ 0.46, Kendall tau ≈ 0.39
- B-campaign pooled rho ≈ 0.95 (identical processing)
- C-campaign pooled rho ≈ 0.09 (swept RecrystT)
- Per-batch rho range: 0.70-0.95
- Spearman partial rho(HV, YS | d) ≈ 0.24 (rank-residual definition)
- Top-K overlaps: 2/5, 8/10, 10/15, 11/20
"""
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression


def test_global_spearman_rho(df_both):
    """Global Spearman rho(HV, YS) = 0.46 (paper §5.7)."""
    rho, p = stats.spearmanr(df_both['HV'], df_both['YS'])
    assert np.isclose(rho, 0.456, atol=0.01), f"rho_global = {rho:.3f}, expected 0.456"
    assert p < 1e-5


def test_global_kendall_tau(df_both):
    """Global Kendall tau(HV, YS) = 0.39 (paper §5.7)."""
    tau, p = stats.kendalltau(df_both['HV'], df_both['YS'])
    assert np.isclose(tau, 0.39, atol=0.01), f"tau = {tau:.3f}, expected 0.39"


def test_B_campaign_rho(df_both):
    """B-campaign (identical processing, n=34) pooled rho = 0.95."""
    b = df_both[df_both['Iteration'].str.startswith('B')]
    rho, _ = stats.spearmanr(b['HV'], b['YS'])
    assert np.isclose(rho, 0.95, atol=0.01), f"rho_B = {rho:.3f}, expected 0.95"
    assert len(b) == 34


def test_C_campaign_rho(df_both):
    """C-campaign (swept RecrystT, n=59) pooled rho collapses to 0.09."""
    c = df_both[df_both['Iteration'].str.startswith('C')]
    rho, _ = stats.spearmanr(c['HV'], c['YS'])
    assert np.isclose(rho, 0.086, atol=0.02), f"rho_C = {rho:.3f}, expected 0.086"
    assert len(c) == 59


def test_per_batch_rho_range(df_both):
    """Per-batch rho range 0.70-0.95."""
    rhos = []
    for batch in sorted(df_both['Iteration'].unique()):
        m = df_both['Iteration'] == batch
        if m.sum() >= 5:
            rho, _ = stats.spearmanr(df_both.loc[m, 'HV'], df_both.loc[m, 'YS'])
            rhos.append(rho)
    assert min(rhos) > 0.69, f"Min within-batch rho = {min(rhos):.3f}"
    assert max(rhos) < 0.96, f"Max within-batch rho = {max(rhos):.3f}"


def test_partial_correlation_HV_YS_given_d(df_both):
    """Spearman partial rho(HV, YS | d) = 0.24, rank-residual definition."""
    r_hv = stats.rankdata(df_both['HV'].values)
    r_ys = stats.rankdata(df_both['YS'].values)
    r_d  = stats.rankdata(df_both['GrainSize'].values)

    def resid(y, x):
        return y - LinearRegression().fit(x.reshape(-1, 1), y).predict(x.reshape(-1, 1))

    rho_partial = stats.pearsonr(resid(r_hv, r_d), resid(r_ys, r_d))[0]
    assert np.isclose(rho_partial, 0.24, atol=0.02), \
        f"partial rho(HV,YS|d) = {rho_partial:.3f}, expected 0.24"


def test_top_K_overlap(df_both):
    """Top-K (HV-ranked vs YS-ranked) overlaps: 2/5, 8/10, 10/15, 11/20."""
    expected = {5: 2, 10: 8, 15: 10, 20: 11}
    for K, exp_overlap in expected.items():
        top_hv = set(df_both.nlargest(K, 'HV').index)
        top_ys = set(df_both.nlargest(K, 'YS').index)
        overlap = len(top_hv & top_ys)
        assert overlap == exp_overlap, \
            f"Top-{K} overlap = {overlap}, expected {exp_overlap}"


def test_d_is_confounder_not_modifier(df_both):
    """Partial correlation < marginal => d is confounder, not sufficient statistic."""
    r_hv = stats.rankdata(df_both['HV'].values)
    r_ys = stats.rankdata(df_both['YS'].values)
    r_d  = stats.rankdata(df_both['GrainSize'].values)

    def resid(y, x):
        return y - LinearRegression().fit(x.reshape(-1, 1), y).predict(x.reshape(-1, 1))

    rho_marginal = stats.spearmanr(df_both['HV'], df_both['YS'])[0]
    rho_partial = stats.pearsonr(resid(r_hv, r_d), resid(r_ys, r_d))[0]
    assert rho_partial < rho_marginal, (
        "Partial correlation should be smaller than marginal, identifying d as "
        "a confounder. This is the §5.7 mechanism claim."
    )


def test_C_eff_log_model_coefficients(df_both):
    """Eq. eq:Ceff_d_V: log(C_eff) = 1.36 + 0.10*log(d) - 2.06*V_frac, R^2 = 0.27."""
    import pandas as pd
    hv_mpa = df_both['HV'].values * 9.807
    log_C = np.log(hv_mpa / df_both['YS'].values)
    X = np.column_stack([np.log(df_both['GrainSize'].values), df_both['V_frac'].values])
    m = LinearRegression().fit(X, log_C)
    r2 = m.score(X, log_C)
    assert np.isclose(m.intercept_, 1.36, atol=0.05), \
        f"intercept = {m.intercept_:.3f}, expected 1.36"
    assert np.isclose(m.coef_[0], 0.10, atol=0.02), \
        f"b (log d) = {m.coef_[0]:.3f}, expected 0.10"
    assert np.isclose(m.coef_[1], -2.06, atol=0.10), \
        f"g (V_frac) = {m.coef_[1]:.3f}, expected -2.06"
    assert np.isclose(r2, 0.27, atol=0.02), f"R^2 = {r2:.3f}, expected 0.27"
