import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from predictor.models import EloModel, LeakageError
from predictor.models.elo import goal_diff_multiplier
from predictor.models.ordered_logit import OrderedLogit
from predictor.ratings.elo import EloRatings


def test_elo_ratings_zero_sum_and_direction():
    r = EloRatings(k=20, home_advantage=50)
    d = r.update("A", "B", 1.0)
    assert d == 50
    assert r.get("A") > 1500 > r.get("B")
    assert r.get("A") + r.get("B") == pytest.approx(3000)
    # expected score is symmetric
    assert r.expected(100) + r.expected(-100) == pytest.approx(1)


def test_elo_draw_moves_favourite_down():
    r = EloRatings(k=20, ratings={"A": 1600, "B": 1400})
    r.update("A", "B", 0.5)
    assert r.get("A") < 1600 and r.get("B") > 1400


def test_goal_diff_multiplier_monotonic():
    vals = [goal_diff_multiplier(g) for g in range(0, 7)]
    assert vals[0] == vals[1] == 1.0 and vals[2] == 1.5
    assert all(b >= a for a, b in zip(vals, vals[1:]))
    assert goal_diff_multiplier(-3) == goal_diff_multiplier(3)


def test_ordered_logit_recovers_parameters():
    rng = np.random.default_rng(0)
    x = rng.normal(size=20000)
    true = np.array([1.2, -0.8, np.log(1.1)])
    p = OrderedLogit._proba(true, x)
    y = np.array([rng.choice(3, p=row) for row in p])
    est = OrderedLogit().fit(x, y).params
    assert est == pytest.approx(true, abs=0.08)


def test_ordered_logit_probabilities_valid():
    m = OrderedLogit()
    p = m.predict_proba(np.linspace(-5, 5, 11))
    assert (p > 0).all() and np.allclose(p.sum(axis=1), 1)
    assert (np.diff(p[:, 2]) > 0).all()  # home prob increases with x


def test_elo_model_ranks_teams(sim):
    df, truth = sim
    m = EloModel(burn_in_days=0).fit(df)
    table = m.ratings_table("XX").set_index("team")["rating"]
    strength = pd.Series(truth["attack"] - truth["defence"], index=truth["teams"])
    rho, _ = spearmanr(table[strength.index], strength)
    assert rho > 0.85


def test_elo_model_predict_shape_and_sanity(sim):
    df, truth = sim
    m = EloModel(burn_in_days=0).fit(df)
    best, worst = truth["teams"][0], truth["teams"][-1]
    fx = pd.DataFrame({"league": ["XX", "XX"], "date": [pd.Timestamp("2023-01-01")] * 2,
                       "home": [best, worst], "away": [worst, best]})
    p = m.predict(fx)
    assert np.allclose(p[["p_home", "p_draw", "p_away"]].sum(axis=1), 1)
    assert p.loc[0, "p_home"] > 0.6 and p.loc[1, "p_away"] > p.loc[1, "p_home"]


def test_elo_fit_as_of_excludes_future(sim):
    df, _ = sim
    cutoff = pd.Timestamp("2020-08-01")
    m = EloModel().fit(df, as_of=cutoff)
    assert m.fitted_until < cutoff
    future = df[df["date"] >= cutoff].head(3)[["league", "date", "home", "away"]]
    m.predict(future)  # ok
    with pytest.raises(LeakageError):
        m.predict(df[df["date"] < cutoff].tail(1)[["league", "date", "home", "away"]])


def test_elo_incremental_fit_matches_full_refit(sim):
    df, _ = sim
    inc = EloModel()
    for cutoff in pd.date_range("2020-09-01", "2021-03-01", freq="30D"):
        inc.fit(df, as_of=cutoff)
    full = EloModel().fit(df, as_of=cutoff)
    assert inc.elo.ratings == pytest.approx(full.elo.ratings)
    assert inc.pooled.params == pytest.approx(full.pooled.params, abs=1e-3)


def test_elo_new_team_starts_below_league_mean(sim):
    df, _ = sim
    m = EloModel(new_team_offset=-100).fit(df)
    fx = pd.DataFrame({"league": ["XX"], "date": [pd.Timestamp("2022-09-01")],
                       "home": ["Newcomers"], "away": ["T05"]})
    diff = m.rating_diffs(fx)[0]
    assert diff < m.params["home_advantage"]  # weaker than an average-ish side


def test_elo_season_regression_applied_for_next_season_fixture(sim):
    df, truth = sim
    m = EloModel(season_regression=0.5).fit(df)
    best, worst = truth["teams"][0], truth["teams"][-1]
    same = pd.DataFrame({"league": ["XX"], "date": [pd.Timestamp("2022-06-01")], "home": [best], "away": [worst]})
    nxt = same.assign(date=pd.Timestamp("2022-08-15"))  # next season, not yet in the data
    view_now, _ = m._rating_view("XX", "2021-22")
    view_next, _ = m._rating_view("XX", "2022-23")
    gap_now = view_now[f"XX:{best}"] - view_now[f"XX:{worst}"]
    gap_next = view_next[f"XX:{best}"] - view_next[f"XX:{worst}"]
    assert gap_next == pytest.approx(gap_now * 0.5)
    assert m.predict(nxt)["p_home"].iat[0] < m.predict(same)["p_home"].iat[0] - 0.02


def test_relegated_club_starts_strong_promoted_weak(sim):
    from conftest import simulate_league
    from predictor.models import DixonColesModel

    top, truth = simulate_league("TOP", seed=3)
    low, _ = simulate_league("LOW", seed=4)
    low = low.assign(home=low["home"].str.replace("T", "L"), away=low["away"].str.replace("T", "L"))
    df = pd.concat([top, low]).sort_values(["date", "league", "home"], kind="stable").reset_index(drop=True)
    tiers = {"LOW": "TOP"}
    relegated, promoted = truth["teams"][-1], "Newcomers"  # T11 (weakest in TOP) drops into LOW
    fx = pd.DataFrame({"league": ["LOW", "LOW"], "date": [pd.Timestamp("2022-08-20")] * 2,
                       "home": [relegated, promoted], "away": ["L05", "L05"]})

    elo = EloModel(tiers=tiers).fit(df)
    d_rel, d_pro = elo.rating_diffs(fx)
    assert d_rel - d_pro == pytest.approx(elo.params["relegated_offset"] - elo.params["new_team_offset"])

    dc = DixonColesModel(tiers=tiers).fit(df)
    p = dc.predict(fx)
    assert p.loc[0, "p_home"] > p.loc[1, "p_home"]
    assert relegated in dc.leagues["LOW"].relegated
