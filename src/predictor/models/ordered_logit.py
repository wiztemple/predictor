"""Ordered logit for three ordered outcomes (away < draw < home).

    P(away)          = sigmoid(c1 - beta * x)
    P(away or draw)  = sigmoid(c2 - beta * x),   c2 = c1 + exp(log_gap) > c1

Used to turn a single strength difference x into home/draw/away probabilities.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

AWAY, DRAW, HOME = 0, 1, 2


class OrderedLogit:
    def __init__(self) -> None:
        self.params = np.array([1.0, -0.6, 0.0])  # beta, c1, log_gap

    @staticmethod
    def _proba(params: np.ndarray, x: np.ndarray) -> np.ndarray:
        beta, c1, log_gap = params
        c2 = c1 + np.exp(log_gap)
        p_a = expit(c1 - beta * x)
        p_ad = expit(c2 - beta * x)
        return np.column_stack([p_a, p_ad - p_a, 1.0 - p_ad])

    def fit(self, x: np.ndarray, y: np.ndarray, weights: np.ndarray | None = None) -> "OrderedLogit":
        x = np.asarray(x, float)
        y = np.asarray(y, int)
        w = np.ones_like(x) if weights is None else np.asarray(weights, float)

        def nll(params):
            p = self._proba(params, x)[np.arange(len(y)), y]
            return -np.sum(w * np.log(np.clip(p, 1e-12, None))) / w.sum()

        # warm start from current params (cheap when refitting week by week)
        res = minimize(nll, self.params, method="BFGS")
        self.params = res.x
        return self

    def predict_proba(self, x) -> np.ndarray:
        """Columns: away, draw, home."""
        return self._proba(self.params, np.atleast_1d(np.asarray(x, float)))
