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
