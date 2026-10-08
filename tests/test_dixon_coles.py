import numpy as np
import pandas as pd
import pytest
from scipy.optimize import approx_fprime

from predictor.models import DixonColesModel, LeakageError
from predictor.models.dixon_coles import markets_from_grid, neg_log_lik, score_grid, tau


def test_tau_values():
    lam, mu, rho = 1.5, 1.1, -0.1
    assert tau(0, 0, lam, mu, rho) == pytest.approx(1 - lam * mu * rho)
    assert tau(0, 1, lam, mu, rho) == pytest.approx(1 + lam * rho)
    assert tau(1, 0, lam, mu, rho) == pytest.approx(1 + mu * rho)
    assert tau(1, 1, lam, mu, rho) == pytest.approx(1 - rho)
    assert tau(2, 3, lam, mu, rho) == 1


def test_gradient_matches_numerical():
    rng = np.random.default_rng(3)
    n, m = 6, 200
    hi = rng.integers(0, n, m)
    ai = (hi + rng.integers(1, n, m)) % n
    x = rng.poisson(1.4, m).astype(float)
    y = rng.poisson(1.1, m).astype(float)
    w = rng.uniform(0.2, 1, m)
    theta = rng.normal(0, 0.2, 3 + 2 * n)
    theta[2] = -0.08
    f = lambda t: neg_log_lik(t, hi, ai, x, y, w, n, 0.7)[0]
    num = approx_fprime(theta, f, 1e-6)
    _, ana = neg_log_lik(theta, hi, ai, x, y, w, n, 0.7)
    assert ana == pytest.approx(num, rel=1e-4, abs=1e-4)


def test_score_grid_and_markets():
    grid = score_grid(1.6, 1.1, -0.1, 10)
    assert grid.sum() == pytest.approx(1)
    mk = markets_from_grid(grid, top_n=5)
    assert mk["p_home"] + mk["p_draw"] + mk["p_away"] == pytest.approx(1)
    assert mk["p_home"] > mk["p_away"]
    assert mk["exp_home_goals"] == pytest.approx(1.6, abs=0.05)
    assert 0 < mk["p_over_2_5"] < 1 and 0 < mk["p_btts"] < 1
    assert 1 > mk["p_over_1_5"] > mk["p_over_2_5"] > mk["p_over_3_5"] > 0
    i, j = np.indices(grid.shape)
    assert mk["p_over_1_5"] == pytest.approx(1 - grid[i + j <= 1].sum())
    tops = mk["top_scorelines"]
    assert len(tops) == 5 and tops[0]["p"] >= tops[-1]["p"]
    assert tops[0]["p"] == pytest.approx(grid.max())


def test_negative_rho_raises_draw_probability_of_low_scores():
    g0 = score_grid(1.3, 1.1, 0.0, 10)
    g1 = score_grid(1.3, 1.1, -0.15, 10)
    assert g1[0, 0] > g0[0, 0] and g1[1, 1] > g0[1, 1]
    assert g1[1, 0] < g0[1, 0]


def test_recovers_simulated_parameters(sim):
    df, truth = sim
    m = DixonColesModel(half_life_days=10_000, l2_penalty=0.01, max_history_days=10_000).fit(df)
    lf = m.leagues["XX"]
    assert lf.home == pytest.approx(truth["home"], abs=0.08)
    att = pd.Series(lf.attack, index=lf.teams)[truth["teams"]].to_numpy()
    dfn = pd.Series(lf.defence, index=lf.teams)[truth["teams"]].to_numpy()
    # identifiable up to a constant shift
    assert np.corrcoef(att, truth["attack"])[0, 1] > 0.9
    assert np.corrcoef(dfn, truth["defence"])[0, 1] > 0.85
    assert abs(lf.rho) < 0.15


def test_time_decay_downweights_old_matches(sim):
    df, truth = sim
    # flip results in the last season: the worst team becomes the best
    flipped = df.copy()
    last = flipped["season"] == "2021-22"
    best, worst = truth["teams"][0], truth["teams"][-1]
    flipped.loc[last, ["home", "away"]] = flipped.loc[last, ["home", "away"]].replace({best: worst, worst: best}).values
    short = DixonColesModel(half_life_days=60).fit(flipped).team_table("XX").set_index("team")
    long = DixonColesModel(half_life_days=5000).fit(flipped).team_table("XX").set_index("team")
    assert short.loc[worst, "net"] - short.loc[best, "net"] > long.loc[worst, "net"] - long.loc[best, "net"]


def test_predict_interface_and_leakage_guard(sim_two_leagues):
    df = sim_two_leagues
    cutoff = pd.Timestamp("2021-06-01")
    m = DixonColesModel().fit(df, as_of=cutoff)
    assert set(m.leagues) == {"AA", "BB"}
    fx = df[df["date"] >= cutoff].head(6)[["league", "date", "home", "away"]]
    p = m.predict(fx)
    for col in ["p_home", "p_draw", "p_away", "p_over_2_5", "p_btts", "top_scorelines", "exp_home_goals"]:
        assert col in p.columns
    assert np.allclose(p[["p_home", "p_draw", "p_away"]].sum(axis=1), 1)
    with pytest.raises(LeakageError):
        m.predict(df[df["date"] < cutoff].tail(1)[["league", "date", "home", "away"]])


def test_unknown_team_gets_weak_prior(sim):
    df, _ = sim
    m = DixonColesModel().fit(df)
    fx = pd.DataFrame({"league": ["XX", "XX"], "date": [pd.Timestamp("2023-01-01")] * 2,
                       "home": ["Newcomers", "T05"], "away": ["T05", "T06"]})
    p = m.predict(fx)
    assert p.loc[0, "p_home"] < p.loc[1, "p_home"]
