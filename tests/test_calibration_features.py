import warnings

import numpy as np
import pandas as pd
import pytest

from predictor.calibration import (
    IsotonicCalibrator,
    PlattCalibrator,
    expected_calibration_error,
    reliability_table,
)
from predictor.features import form_features, involves_promoted_team
from predictor.metrics import cluster_bootstrap_mean, log_loss
from predictor.stacking import BASE_FEATURES, walk_forward_gbm

OUT = np.array(["H", "D", "A"])


def _overconfident(n=6000, seed=0):
    """True probs from a Dirichlet; reported probs are sharpened (overconfident)."""
    rng = np.random.default_rng(seed)
    true = rng.dirichlet([4, 3, 3], n)
    y = np.array([rng.choice(3, p=p) for p in true])
    sharp = true ** 2
    sharp /= sharp.sum(axis=1, keepdims=True)
    return sharp, OUT[y]


@pytest.mark.parametrize("cls", [IsotonicCalibrator, PlattCalibrator])
def test_calibrators_fix_overconfidence_out_of_sample(cls):
    p_fit, y_fit = _overconfident(seed=0)
    p_new, y_new = _overconfident(seed=1)
    cal = cls().fit(p_fit, y_fit)
    out = cal.transform(p_new)
    assert np.allclose(out.sum(axis=1), 1) and (out > 0).all()
    assert log_loss(out, y_new) < log_loss(p_new, y_new) - 0.01


def test_platt_emits_no_runtime_warnings():
    p, y = _overconfident(n=2000)
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        PlattCalibrator().fit(p, y).transform(p)


def test_reliability_table_and_ece():
    p, y = _overconfident()
    tab = reliability_table(p, y, n_bins=10)
    assert set(tab["outcome"]) == {"home", "draw", "away"}
    assert tab.groupby("outcome")["n"].sum().eq(len(p)).all()
    ece_bad = expected_calibration_error(tab)
    ece_good = expected_calibration_error(reliability_table(IsotonicCalibrator().fit(p, y).transform(p), y))
    assert ece_good["home"] < ece_bad["home"]


def test_cluster_bootstrap_ci_contains_mean():
    v = np.random.default_rng(0).normal(0.02, 0.5, 3000)
    m, lo, hi = cluster_bootstrap_mean(v, np.arange(3000) // 10)
    assert lo < m < hi and lo < 0.02 < hi


def test_form_features_use_only_past_matches():
    m = pd.DataFrame({
        "league": "XX", "season": "2020-21",
        "date": pd.to_datetime(["2020-08-01", "2020-08-08", "2020-08-15", "2020-08-22"]),
        "home": ["A", "B", "A", "C"], "away": ["B", "A", "C", "A"],
        "home_score": [2, 0, 1, 0], "away_score": [0, 0, 1, 3],
    })
    f = form_features(m, window=5)
    assert np.isnan(f.loc[0, "home_form_pts"])          # no history yet
    assert f.loc[1, "away_form_pts"] == 3                 # A won match 0
    assert f.loc[2, "home_form_pts"] == pytest.approx(2)  # A: W, D -> 4/2
    assert f.loc[3, "away_rest_days"] == 7
    assert f.loc[3, "away_n_prev"] == 3


def test_promoted_flag():
    rows = []
    for season, teams in (("2019-20", ["A", "B", "C"]), ("2020-21", ["A", "B", "D"])):
        for h in teams:
            for a in teams:
                if h != a:
                    rows.append(("XX", season, h, a))
    m = pd.DataFrame(rows, columns=["league", "season", "home", "away"])
    flag = involves_promoted_team(m)
    assert not flag[m["season"] == "2019-20"].any()  # first season: unknown, never flagged
    s2 = m["season"] == "2020-21"
    assert (flag[s2] == ((m["home"] == "D") | (m["away"] == "D"))[s2]).all()


def test_walk_forward_gbm_trains_on_past_only():
    rng = np.random.default_rng(0)
    n = 1200
    t = pd.DataFrame(rng.normal(size=(n, len(BASE_FEATURES))), columns=BASE_FEATURES)
    t["date"] = pd.date_range("2020-01-01", periods=n, freq="D")
    t["outcome"] = OUT[rng.integers(0, 3, n)]
    test_mask = t["date"] >= "2022-09-01"
    out = walk_forward_gbm(t, BASE_FEATURES, test_mask, pd.Series(True, index=t.index))
    assert out.index.equals(t.index[test_mask])
    assert np.allclose(out.sum(axis=1), 1)


def _binary_overconfident(n=8000, seed=0):
    rng = np.random.default_rng(seed)
    true = rng.uniform(0.2, 0.8, n)
    y = (rng.uniform(size=n) < true).astype(int)
    reported = 1 / (1 + np.exp(-2 * np.log(true / (1 - true))))  # sharpened
    return reported, y


@pytest.mark.parametrize("method", ["platt", "isotonic"])
def test_binary_calibrators_improve_and_roundtrip(method):
    from predictor.calibration import BINARY_CALIBRATORS, binary_from_dict
    from predictor.metrics import binary_scores

    p_fit, y_fit = _binary_overconfident(seed=0)
    p_new, y_new = _binary_overconfident(seed=1)
    cal = BINARY_CALIBRATORS[method]().fit(p_fit, y_fit)
    out = cal.transform(p_new)
    assert binary_scores(out, y_new)["log_loss"] < binary_scores(p_new, y_new)["log_loss"] - 0.01
    again = binary_from_dict(cal.to_dict()).transform(p_new)
    assert np.allclose(out, again)


def test_goals_calibration_keeps_lines_ordered():
    from predictor.calibration import apply_goals_calibration

    probs = {"over_1_5": np.array([0.70]), "over_2_5": np.array([0.60]), "over_3_5": np.array([0.40])}
    # a calibrator that pushes over 2.5 above over 1.5's raw value
    cals = {"over_2_5": {"method": "platt", "a": 1.0, "b": 1.0}}
    out = apply_goals_calibration(probs, cals)
    assert out["over_1_5"][0] >= out["over_2_5"][0] >= out["over_3_5"][0]
