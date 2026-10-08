"""Probability scoring for 3-way (home/draw/away) predictions."""
from __future__ import annotations

import numpy as np
import pandas as pd

OUTCOME_INDEX = {"H": 0, "D": 1, "A": 2}
PROB_COLS = ["p_home", "p_draw", "p_away"]


def _onehot(outcomes) -> np.ndarray:
    idx = pd.Series(outcomes).map(OUTCOME_INDEX).to_numpy()
    y = np.zeros((len(idx), 3))
    y[np.arange(len(idx)), idx] = 1
    return y


def log_loss(probs: np.ndarray, outcomes) -> float:
    y = _onehot(outcomes)
    return float(-np.mean(np.log(np.clip((probs * y).sum(axis=1), 1e-15, None))))


def brier(probs: np.ndarray, outcomes) -> float:
    """Multiclass Brier score: mean over matches of sum_k (p_k - y_k)^2 (range 0..2)."""
    return float(np.mean(((probs - _onehot(outcomes)) ** 2).sum(axis=1)))


def accuracy(probs: np.ndarray, outcomes) -> float:
    return float(np.mean(probs.argmax(axis=1) == _onehot(outcomes).argmax(axis=1)))


def score(df: pd.DataFrame, prob_cols=PROB_COLS, outcome_col: str = "outcome") -> dict[str, float]:
    p = df[list(prob_cols)].to_numpy(float)
    o = df[outcome_col]
    return {"n": len(df), "log_loss": log_loss(p, o), "brier": brier(p, o), "accuracy": accuracy(p, o)}


def odds_to_probs(odds_home, odds_draw, odds_away) -> np.ndarray:
    """Bookmaker decimal odds -> probabilities with overround removed proportionally."""
    inv = 1.0 / np.column_stack([odds_home, odds_draw, odds_away]).astype(float)
    return inv / inv.sum(axis=1, keepdims=True)


def per_match_log_loss(probs: np.ndarray, outcomes) -> np.ndarray:
    y = _onehot(outcomes)
    return -np.log(np.clip((probs * y).sum(axis=1), 1e-15, None))


def cluster_bootstrap_mean(values: np.ndarray, clusters, n_boot: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Mean and 95% CI, resampling whole clusters (e.g. weeks) since matches in
    the same round aren't independent."""
    df = pd.DataFrame({"v": values, "c": np.asarray(clusters)})
    sums = df.groupby("c")["v"].agg(["sum", "count"])
    s, n = sums["sum"].to_numpy(), sums["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(s), size=(n_boot, len(s)))
    boots = s[idx].sum(axis=1) / n[idx].sum(axis=1)
    return float(values.mean()), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def binary_scores(p: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """Log loss and Brier for a yes/no market (p = P(yes), y in {0, 1})."""
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    y = np.asarray(y, float)
    return {
        "n": int(len(p)),
        "log_loss": float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p))),
        "brier": float(np.mean((p - y) ** 2)),
    }


def binary_reliability(p: np.ndarray, y: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    edges = np.linspace(0, 1, n_bins + 1)
    b = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    rows = []
    for i in range(n_bins):
        m = b == i
        if m.any():
            rows.append({"bin_lo": edges[i], "bin_hi": edges[i + 1], "n": int(m.sum()),
                         "mean_pred": float(p[m].mean()), "observed": float(y[m].mean())})
    return pd.DataFrame(rows)
