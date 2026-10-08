import pandas as pd
import pytest

from predictor.picks import best_pick, candidates, closing_odds, rank_by_day, won

PROBS = {"home": 0.55, "draw": 0.25, "away": 0.20}
EXTRAS = {"over_1_5": 0.78, "over_2_5": 0.55, "over_3_5": 0.30, "btts": 0.52}


def test_candidates_cover_all_markets_and_sum_correctly():
    cs = candidates("A", "B", PROBS, EXTRAS)
    assert {c.market for c in cs} == {"1x2", "double_chance", "ou_1_5", "ou_2_5", "ou_3_5", "btts"}
    by = {(c.market, c.selection): c.p for c in cs}
    assert by[("double_chance", "1x")] == pytest.approx(0.80)
    assert by[("ou_3_5", "under")] == pytest.approx(0.70)
    for mk in ("ou_1_5", "ou_2_5", "btts"):
        assert sum(c.p for c in cs if c.market == mk) == pytest.approx(1)


def test_best_pick_is_most_likely_across_markets():
    b = best_pick("A", "B", PROBS, EXTRAS)
    assert (b.market, b.selection, b.label) == ("double_chance", "1x", "A or draw")
    assert best_pick("A", "B", PROBS, EXTRAS, markets=("1x2", "ou_2_5")).selection == "home"
    assert best_pick("A", "B", PROBS, {}, markets=("btts",)) is None


@pytest.mark.parametrize("market,sel,score,expected", [
    ("1x2", "home", (2, 1), True), ("1x2", "draw", (1, 1), True), ("1x2", "away", (1, 1), False),
    ("double_chance", "1x", (1, 1), True), ("double_chance", "12", (0, 0), False), ("double_chance", "x2", (0, 2), True),
    ("ou_1_5", "over", (1, 1), True), ("ou_1_5", "over", (1, 0), False), ("ou_2_5", "under", (2, 0), True),
    ("ou_3_5", "under", (2, 2), False), ("btts", "yes", (1, 1), True), ("btts", "no", (3, 0), True),
])
def test_settlement(market, sel, score, expected):
    assert won(market, sel, *score) is expected


def test_closing_odds_only_where_real():
    row = {"odds_home": 1.8, "odds_draw": 3.6, "odds_away": 4.5, "odds_over_2_5": 1.9, "odds_under_2_5": float("nan")}
    assert closing_odds("1x2", "home", row) == 1.8
    assert closing_odds("ou_2_5", "over", row) == 1.9
    assert closing_odds("ou_2_5", "under", row) is None
    assert closing_odds("double_chance", "1x", row) is None


def test_rank_by_day_uses_uk_day():
    df = pd.DataFrame({"kickoff": ["2026-10-10T14:00:00Z", "2026-10-10T19:00:00Z", "2026-10-10T23:30:00Z"],
                       "probability": [0.7, 0.9, 0.95]})
    # 23:30Z is 00:30 on 11 Oct in UK time -> its own day
    assert list(rank_by_day(df)) == [2, 1, 1]


from predictor.picks import settle_state, weekly_candidate  # noqa: E402

MARGIN = {"cap": 6, "probs": [0.002, 0.005, 0.015, 0.04, 0.08, 0.13, 0.25, 0.2, 0.13, 0.08, 0.04, 0.02, 0.008]}


@pytest.mark.parametrize("spec,check", [
    ({"kind": "any"}, lambda s: s.p >= 0.75),
    ({"kind": "band", "min_odds": 1.30, "max_odds": 1.60}, lambda s: 1 / 1.60 <= s.p <= 1 / 1.30),
    ({"kind": "band", "min_odds": 1.60, "max_odds": 2.00}, lambda s: 0.5 <= s.p <= 1 / 1.60),
    ({"kind": "wins"}, lambda s: s.market == "1x2" and s.selection in ("home", "away")),
    ({"kind": "over25"}, lambda s: (s.market, s.selection) == ("ou_2_5", "over")),
    ({"kind": "btts"}, lambda s: (s.market, s.selection) == ("btts", "yes")),
    ({"kind": "ah", "min_odds": 1.70, "max_odds": 2.10}, lambda s: s.market == "ah" and 1 / 2.10 <= s.p <= 1 / 1.70),
])
def test_weekly_candidates(spec, check):
    s = weekly_candidate("A", "B", PROBS, {**EXTRAS, "margin": MARGIN}, spec)
    assert s is not None and check(s)


def test_band_with_no_qualifying_selection():
    assert weekly_candidate("A", "B", PROBS, EXTRAS, {"kind": "band", "min_odds": 20.0, "max_odds": 30.0}) is None


@pytest.mark.parametrize("sel,score,state", [
    ("home:-0.5", (1, 0), "won"), ("home:-1", (1, 0), "push"), ("home:-0.75", (1, 0), "half_won"),
    ("home:-0.25", (1, 1), "half_lost"), ("away:0.25", (1, 1), "half_won"), ("away:1.5", (2, 0), "lost"),
])
def test_ah_settlement(sel, score, state):
    assert settle_state("ah", sel, *score) == state


def test_non_ah_settlement():
    assert settle_state("1x2", "home", 2, 1) == "won" and settle_state("btts", "yes", 1, 0) == "lost"
