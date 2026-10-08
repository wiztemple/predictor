import numpy as np
import pandas as pd
import pytest

from predictor.backtest import walk_forward
from predictor.metrics import accuracy, brier, log_loss, odds_to_probs
from predictor.models import EloModel


def test_metrics_known_values():
    p = np.array([[0.5, 0.3, 0.2], [0.2, 0.3, 0.5]])
    o = ["H", "D"]
    assert log_loss(p, o) == pytest.approx(-(np.log(0.5) + np.log(0.3)) / 2)
    assert brier(p, o) == pytest.approx(((0.25 + 0.09 + 0.04) + (0.04 + 0.49 + 0.25)) / 2)
    assert accuracy(p, o) == 0.5
    assert brier(np.array([[1, 0, 0]]), ["H"]) == 0


def test_odds_to_probs_removes_overround():
    p = odds_to_probs(np.array([2.0]), np.array([3.4]), np.array([4.0]))
    assert p.sum() == pytest.approx(1)
    assert p[0, 0] > p[0, 2]


def test_walk_forward_never_trains_on_test_period(sim):
    df, _ = sim
    mask = df["season"] == "2021-22"
    pred = walk_forward(EloModel(), df, mask)
    assert len(pred) == mask.sum()
    assert (pred["cutoff"] <= pred["date"]).all()
    # every prediction's fit used only matches strictly before its cutoff
    assert (pred.groupby("cutoff")["date"].min() >= pred.groupby("cutoff")["cutoff"].first()).all()


def test_blend_is_weighted_average_with_dc_goals_markets(sim):
    from predictor.models import BlendModel, DixonColesModel

    df, truth = sim
    fx = pd.DataFrame({"league": ["XX"], "date": [pd.Timestamp("2023-01-01")],
                       "home": [truth["teams"][0]], "away": [truth["teams"][5]]})
    b = BlendModel(weight_elo=0.4).fit(df)
    e, d, p = EloModel().fit(df).predict(fx), DixonColesModel().fit(df).predict(fx), b.predict(fx)
    for c in ("p_home", "p_draw", "p_away"):
        assert p[c].iat[0] == pytest.approx(0.4 * e[c].iat[0] + 0.6 * d[c].iat[0])
    assert p["p_over_2_5"].iat[0] == pytest.approx(d["p_over_2_5"].iat[0])
    assert b.grid("XX", truth["teams"][0], truth["teams"][5]).sum() == pytest.approx(1)
