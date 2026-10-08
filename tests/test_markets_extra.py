import numpy as np
import pytest

from predictor.markets_extra import adjust_grid, all_markets, full_time_markets, half_grid, half_time_markets, settle
from predictor.models.dixon_coles import score_grid

P1X2 = (0.50, 0.27, 0.23)
GOALS = {"over_1_5": 0.74, "over_2_5": 0.50, "over_3_5": 0.27, "btts": 0.52}


def test_adjusted_grid_hits_every_target():
    g = adjust_grid(score_grid(1.5, 1.1, -0.08, 10), P1X2, GOALS)
    i, j = np.indices(g.shape)
    assert g.sum() == pytest.approx(1)
    assert g[i > j].sum() == pytest.approx(0.50, abs=1e-6) and g[i == j].sum() == pytest.approx(0.27, abs=1e-6)
    assert g[i + j >= 3].sum() == pytest.approx(0.50, abs=1e-6)
    assert g[(i >= 1) & (j >= 1)].sum() == pytest.approx(0.52, abs=1e-6)


def test_full_time_markets_consistent():
    g = adjust_grid(score_grid(1.5, 1.1, -0.08, 10), P1X2, GOALS)
    m = full_time_markets(g)
    for key in ("result_btts", "result_ou25", "exact_goals", "odd_even", "home_ou0_5"):
        assert sum(m[key].values()) == pytest.approx(1)
    assert m["result_btts"]["1&GG"] + m["result_btts"]["1&NG"] == pytest.approx(0.50, abs=1e-6)
    assert m["result_ou25"]["1&O"] + m["result_ou25"]["X&O"] + m["result_ou25"]["2&O"] == pytest.approx(0.50, abs=1e-6)
    assert m["clean_sheet"]["home"] == pytest.approx(m["away_ou0_5"]["under"])
    assert m["win_to_nil"]["home"] <= min(m["clean_sheet"]["home"], 0.50)
    assert m["dnb"]["1"] == pytest.approx(0.50 / 0.73)


def test_half_time_markets_and_ft_consistency():
    P = half_grid(1.5, 1.1, 0.445, P1X2)
    m = half_time_markets(P)
    assert sum(m["htft"].values()) == pytest.approx(1) and sum(m["ht_result"].values()) == pytest.approx(1)
    # full-time column of HT/FT matches the published 1X2
    assert sum(v for k, v in m["htft"].items() if k.endswith("/1")) == pytest.approx(0.50, abs=1e-9)
    assert m["htft"]["1/1"] > m["htft"]["2/1"]
    assert m["ht_result"]["X"] > 0.3
    assert sum(m["highest_half"].values()) == pytest.approx(1)
    assert m["highest_half"]["2nd"] > m["highest_half"]["1st"]  # 55.5% of goals come after the break


def test_all_markets_and_settlement():
    g, m = all_markets(1.5, 1.1, -0.08, P1X2, GOALS, 0.445)
    assert set(m) >= {"result_btts", "htft", "dnb", "exact_goals"}
    assert settle("result_btts", 2, 1) == "1&GG"
    assert settle("result_ou25", 1, 1) == "X&U"
    assert settle("exact_goals", 3, 3) == "5+"
    assert settle("home_ou1_5", 1, 0) == "under"
    assert settle("win_to_nil", 2, 0) == {"home": True, "away": False}
    assert settle("htft", 2, 1, 0, 1) == "2/1"
    assert settle("highest_half", 2, 1, 0, 0) == "2nd"
    assert settle("ht_result", 1, 0, float("nan"), 0) is None
