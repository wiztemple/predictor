"""Asian handicap from a goal-difference distribution.

A line is the HOME team's handicap, e.g. -0.75 = home gives 0.75 goals.
  half lines  (-0.5, -1.5)  win / lose
  whole lines (-1, -2)      win / push (stake back) / lose
  quarter lines (-0.75)     stake split equally over the two neighbouring lines
The away side of home line L is the away team at +... i.e. it wins exactly when home loses.
"""
from __future__ import annotations

import numpy as np

from predictor.models.dixon_coles import MARGIN_CAP


def rescale_margins(margin: np.ndarray, p_home: float, p_draw: float, p_away: float, cap: int = MARGIN_CAP) -> np.ndarray:
    """Rescale a margin distribution so P(>0), P(=0), P(<0) match the given 1X2
    (keeps the shape within each part; makes AH -0.5 agree with the published home win)."""
    m = np.asarray(margin, float).copy()
    k = np.arange(-cap, cap + 1)
    for mask, target in ((k > 0, p_home), (k == 0, p_draw), (k < 0, p_away)):
        s = m[mask].sum()
        if s > 0:
            m[mask] *= target / s
    return m / m.sum()


def _split(line: float) -> tuple[float, float]:
    """Quarter lines split into two halves; other lines are a single line twice."""
    q = round(line * 4)
    if q % 2 != 0:  # x.25 / x.75
        return (q - 1) / 4, (q + 1) / 4
    return line, line


def home_outcome(margin: np.ndarray, line: float, cap: int = MARGIN_CAP) -> tuple[float, float, float]:
    """(win, push, lose) for HOME at `line`, as stake-weighted probabilities (halves count half)."""
    k = np.arange(-cap, cap + 1)
    w = p = l = 0.0
    for part in _split(line):
        adj = k + part
        w += margin[adj > 0].sum() / 2
        p += margin[np.isclose(adj, 0)].sum() / 2
        l += margin[adj < 0].sum() / 2
    return float(w), float(p), float(l)


def fair_odds(win: float, lose: float) -> float:
    """Decimal odds with zero expected value when pushes return the stake: 1 + lose / win."""
    return float("inf") if win <= 0 else 1 + lose / win


def main_line(margin: np.ndarray, lo: float = -3.0, hi: float = 3.0) -> float:
    """The quarter-step home line whose fair odds are closest to evens (2.0), like a bookmaker's main line."""
    lines = np.arange(lo, hi + 1e-9, 0.25)
    best, gap = 0.0, np.inf
    for line in lines:
        w, _, l = home_outcome(margin, float(line))
        g = abs(np.log(fair_odds(w, l) / 2.0)) if w > 0 and l > 0 else np.inf
        if g < gap - 1e-12:
            best, gap = float(line), g
    return round(best * 4) / 4
