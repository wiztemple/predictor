import numpy as np
import pytest

from predictor.handicap import _split, fair_odds, home_outcome, main_line, rescale_margins
from predictor.models.dixon_coles import MARGIN_CAP, margin_distribution, score_grid

K = np.arange(-MARGIN_CAP, MARGIN_CAP + 1)


def margins_for(lam=1.7, mu=0.9, rho=-0.08):
    return margin_distribution(score_grid(lam, mu, rho, 10))


def test_margin_distribution_matches_grid():
    g = score_grid(1.7, 0.9, -0.08, 10)
    m = margin_distribution(g)
    i, j = np.indices(g.shape)
    assert m.sum() == pytest.approx(1)
    assert m[K > 0].sum() == pytest.approx(g[i > j].sum())
    assert m[K == 0].sum() == pytest.approx(g[i == j].sum())


def test_split_lines():
    assert _split(-0.75) == (-1.0, -0.5)
    assert _split(-1.0) == (-1.0, -1.0)
    assert _split(0.25) == (0.0, 0.5)


def test_half_whole_and_quarter_lines():
    m = margins_for()
    p_home, p_draw = m[K > 0].sum(), m[K == 0].sum()
    assert home_outcome(m, -0.5) == pytest.approx((p_home, 0, 1 - p_home))     # AH -0.5 = home win
    assert home_outcome(m, 0.0) == pytest.approx((p_home, p_draw, 1 - p_home - p_draw))  # draw no bet
    w, p, l = home_outcome(m, -1.0)
    assert p == pytest.approx(m[K == 1].sum()) and w == pytest.approx(m[K >= 2].sum())
    # quarter line = average of its halves
    a, b = home_outcome(m, -0.5), home_outcome(m, -1.0)
    assert home_outcome(m, -0.75) == pytest.approx(tuple((x + y) / 2 for x, y in zip(a, b)))
    for line in np.arange(-3, 3.01, 0.25):
        assert sum(home_outcome(m, float(line))) == pytest.approx(1)


def test_fair_odds_and_main_line():
    assert fair_odds(0.5, 0.5) == pytest.approx(2.0)
    assert fair_odds(0.4, 0.4) == pytest.approx(2.0)  # 20% push doesn't change evens
    m = margins_for(1.7, 0.9)
    line = main_line(m)
    assert line < 0  # home favourite gives goals
    w, _, l = home_outcome(m, line)
    assert 1.6 < fair_odds(w, l) < 2.5
    assert main_line(margins_for(1.2, 1.2)) in (0.0, -0.25, 0.25)


def test_rescale_matches_target_1x2():
    m = rescale_margins(margins_for(), 0.5, 0.3, 0.2)
    assert m[K > 0].sum() == pytest.approx(0.5) and m[K == 0].sum() == pytest.approx(0.3)
    assert home_outcome(m, -0.5)[0] == pytest.approx(0.5)
