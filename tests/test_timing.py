import math

import pytest

from predictor.timing import early_result


def test_probabilities_and_zero_zero():
    r = early_result(1.6, 1.1, 0.085)
    assert r["home"] + r["draw"] + r["away"] == pytest.approx(1)
    assert r["no_goal"] == pytest.approx(math.exp(-(1.6 + 1.1) * 0.085), rel=1e-6)
    assert r["draw"] > r["no_goal"] > 0.7  # level after 10' is almost always 0-0
    assert r["home"] > r["away"]


def test_longer_window_means_fewer_draws():
    assert early_result(1.5, 1.2, 0.445)["draw"] < early_result(1.5, 1.2, 0.085)["draw"]
    assert early_result(1.5, 1.2, 1e-9)["draw"] == pytest.approx(1)
