"""Calibration of 3-way probabilities and reliability diagnostics.

Calibrators are fitted on predictions for EARLIER matches and applied to later
ones; callers are responsible for the time split.
"""
from __future__ import annotations

import warnings
from contextlib import contextmanager

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from predictor.metrics import OUTCOME_INDEX, PROB_COLS

_EPS = 1e-6


def _labels(outcomes) -> np.ndarray:
    return pd.Series(outcomes).map(OUTCOME_INDEX).to_numpy()


class IdentityCalibrator:
    name = "none"

    def fit(self, probs: np.ndarray, outcomes) -> "IdentityCalibrator":
        return self

    def transform(self, probs: np.ndarray) -> np.ndarray:
        return probs


class IsotonicCalibrator:
    """One-vs-rest isotonic regression per outcome, then renormalised."""

    name = "isotonic"

    def fit(self, probs: np.ndarray, outcomes) -> "IsotonicCalibrator":
        y = _labels(outcomes)
        self.models = [
            IsotonicRegression(y_min=_EPS, y_max=1 - _EPS, out_of_bounds="clip").fit(probs[:, k], y == k)
            for k in range(3)
        ]
        return self

    def transform(self, probs: np.ndarray) -> np.ndarray:
        out = np.column_stack([m.predict(probs[:, k]) for k, m in enumerate(self.models)])
        out = np.clip(out, _EPS, None)
        return out / out.sum(axis=1, keepdims=True)


class PlattCalibrator:
    """Multinomial logistic regression on log-probabilities ("matrix scaling").

    With weak regularisation this generalises Platt scaling to three classes;
    the identity mapping is inside its family, so it can only shrink or
    sharpen and re-bias the input probabilities.
    """

    name = "platt"

    def __init__(self, C: float = 1.0) -> None:
        self.C = C

    def fit(self, probs: np.ndarray, outcomes) -> "PlattCalibrator":
        with _quiet_matmul():
            self.model = LogisticRegression(C=self.C, max_iter=1000).fit(
                np.log(np.clip(probs, _EPS, 1)), _labels(outcomes)
            )
        return self

    def transform(self, probs: np.ndarray) -> np.ndarray:
        with _quiet_matmul():
            return self.model.predict_proba(np.log(np.clip(probs, _EPS, 1)))


@contextmanager
def _quiet_matmul():
    """numpy 2.0 + Apple Accelerate emits spurious 'divide by zero/overflow in matmul'
    RuntimeWarnings even on well-conditioned inputs; results are finite and correct."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*encountered in matmul", category=RuntimeWarning)
        yield


CALIBRATORS = {"none": IdentityCalibrator, "isotonic": IsotonicCalibrator, "platt": PlattCalibrator}


def reliability_table(probs: np.ndarray, outcomes, n_bins: int = 10) -> pd.DataFrame:
    """Binned predicted vs observed frequency for each outcome (equal-width bins)."""
    y = _labels(outcomes)
    rows = []
    edges = np.linspace(0, 1, n_bins + 1)
    for k, name in enumerate(["home", "draw", "away"]):
        p = probs[:, k]
        b = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
        for i in range(n_bins):
            m = b == i
            if m.any():
                rows.append({
                    "outcome": name, "bin_lo": edges[i], "bin_hi": edges[i + 1], "n": int(m.sum()),
                    "mean_pred": float(p[m].mean()), "observed": float((y[m] == k).mean()),
                })
    return pd.DataFrame(rows)


def expected_calibration_error(table: pd.DataFrame) -> dict[str, float]:
    """Count-weighted |predicted - observed| per outcome."""
    out = {}
    for name, g in table.groupby("outcome", sort=False):
        out[name] = float(np.average((g["mean_pred"] - g["observed"]).abs(), weights=g["n"]))
    return out


def probs_of(df: pd.DataFrame, cols=PROB_COLS) -> np.ndarray:
    return df[list(cols)].to_numpy(float)


# ---------------------------------------------------------------------------
# Binary (yes/no) markets, e.g. over 2.5 goals. Serialisable so the live
# pipeline applies exactly what the backtest fitted.

def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, float), _EPS, 1 - _EPS)
    return np.log(p / (1 - p))


class BinaryIdentity:
    name = "none"

    def fit(self, p, y) -> "BinaryIdentity":
        return self

    def transform(self, p) -> np.ndarray:
        return np.asarray(p, float)

    def to_dict(self) -> dict:
        return {"method": "none"}


class BinaryPlatt:
    """Logistic regression on logit(p): p' = sigmoid(a * logit(p) + b)."""

    name = "platt"

    def fit(self, p, y) -> "BinaryPlatt":
        with _quiet_matmul():
            m = LogisticRegression(C=1e4, max_iter=1000).fit(_logit(p).reshape(-1, 1), np.asarray(y, int))
        self.a, self.b = float(m.coef_[0, 0]), float(m.intercept_[0])
        return self

    def transform(self, p) -> np.ndarray:
        return 1 / (1 + np.exp(-(self.a * _logit(p) + self.b)))

    def to_dict(self) -> dict:
        return {"method": "platt", "a": self.a, "b": self.b}


class BinaryIsotonic:
    name = "isotonic"

    def fit(self, p, y) -> "BinaryIsotonic":
        iso = IsotonicRegression(y_min=_EPS, y_max=1 - _EPS, out_of_bounds="clip").fit(p, y)
        self.x, self.y = iso.X_thresholds_.tolist(), iso.y_thresholds_.tolist()
        return self

    def transform(self, p) -> np.ndarray:
        return np.interp(np.asarray(p, float), self.x, self.y)

    def to_dict(self) -> dict:
        return {"method": "isotonic", "x": self.x, "y": self.y}


BINARY_CALIBRATORS = {"none": BinaryIdentity, "platt": BinaryPlatt, "isotonic": BinaryIsotonic}


def binary_from_dict(d: dict):
    cal = BINARY_CALIBRATORS[d["method"]]()
    if d["method"] == "platt":
        cal.a, cal.b = d["a"], d["b"]
    elif d["method"] == "isotonic":
        cal.x, cal.y = d["x"], d["y"]
    return cal


GOALS_KEYS = ("over_1_5", "over_2_5", "over_3_5", "btts")


def apply_goals_calibration(probs: dict[str, np.ndarray], calibrators: dict) -> dict[str, np.ndarray]:
    """Calibrate each goals market, then restore the ordering
    P(over 1.5) >= P(over 2.5) >= P(over 3.5) that independent calibration can break."""
    out = {k: (binary_from_dict(calibrators[k]).transform(v) if k in calibrators else np.asarray(v, float))
           for k, v in probs.items()}
    if {"over_1_5", "over_2_5", "over_3_5"} <= out.keys():
        out["over_1_5"] = np.maximum(out["over_1_5"], out["over_2_5"])
        out["over_3_5"] = np.minimum(out["over_3_5"], out["over_2_5"])
    return out
