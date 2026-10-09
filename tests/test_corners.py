import numpy as np
import pandas as pd
import pytest

from predictor.corners import (CornersModel, LeagueAverageCorners, fit_dispersion, line_key, over_probs,
                               total_pmf)
from predictor.models.base import LeakageError


def _season(rng, n_rounds=40, strong="A", league="E0", start="2023-08-01"):
    teams = list("ABCDEFGH")
    rows = []
    d = pd.Timestamp(start)
    for r in range(n_rounds):
        order = rng.permutation(teams)
        for h, a in zip(order[::2], order[1::2]):
            mh = 8.0 if h == strong else 4.5
            ma = 8.0 if a == strong else 4.0
            rows.append({"league": league, "date": d, "home": h, "away": a,
                         "home_corners": rng.poisson(mh), "away_corners": rng.poisson(ma)})
        d += pd.Timedelta(days=7)
    return pd.DataFrame(rows)


def test_line_key():
    assert line_key(8.5) == "over_8_5"
    assert line_key(10.5) == "over_10_5"


def test_over_probs_monotone_and_poisson_limit():
    mean = np.array([9.0, 11.0])
    p = over_probs(mean, None)
    assert all(p[7.5] > p[8.5]) and all(p[8.5] > p[9.5])
    assert p[9.5][1] > p[9.5][0]  # higher mean -> more overs
    q = over_probs(mean, 1e6)
    assert np.allclose(p[9.5], q[9.5], atol=1e-4)
    assert np.allclose(total_pmf(mean, 50.0).sum(axis=1), 1.0, atol=1e-6)


def test_dispersion_fit_separates_poisson_from_overdispersed():
    rng = np.random.default_rng(1)
    mean = np.full(4000, 10.0)
    k_pois = fit_dispersion(mean, rng.poisson(10, 4000))
    k_over = fit_dispersion(mean, rng.negative_binomial(5, 5 / 15, 4000))
    assert k_pois > 100 and k_over < 10


def test_model_finds_the_corner_heavy_team():
    rng = np.random.default_rng(0)
    m = _season(rng)
    model = CornersModel(half_life_days=365, l2_penalty=1.0).fit(m)
    fx = pd.DataFrame({"league": ["E0", "E0"], "date": [m["date"].max() + pd.Timedelta(days=3)] * 2,
                       "home": ["A", "B"], "away": ["C", "D"]})
    p = model.predict(fx)
    assert p.loc[0, "exp_home_corners"] > p.loc[1, "exp_home_corners"] + 2
    assert p.loc[0, "p_over_9_5"] > p.loc[1, "p_over_9_5"]


def test_no_corner_data_league_gives_nan_and_leak_guard():
    rng = np.random.default_rng(0)
    m = _season(rng)
    model = CornersModel().fit(m)
    later = m["date"].max() + pd.Timedelta(days=3)
    p = model.predict(pd.DataFrame({"league": ["AUT"], "date": [later], "home": ["X"], "away": ["Y"]}))
    assert np.isnan(p.loc[0, "exp_corners"]) and np.isnan(p.loc[0, "p_over_8_5"])
    with pytest.raises(LeakageError):
        model.predict(m.head(1))


def test_fit_respects_cutoff():
    rng = np.random.default_rng(0)
    m = _season(rng)
    cut = m["date"].iloc[len(m) // 2]
    model = CornersModel().fit(m, as_of=cut)
    assert model.fitted_until < cut
    base = LeagueAverageCorners().fit(m, as_of=cut)
    assert base.fitted_until < cut
    assert 8 < base.means["E0"] < 12
