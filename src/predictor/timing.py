"""Result after the first part of a match (e.g. 10 minutes, half-time).

Goals are treated as arriving at random within the match, so each team's goals
by time t are Poisson with mean (expected match goals) x share(t), where
share(t) is the fraction of a match's goals scored by then. The Dixon-Coles
low-score correction is negligible at these small rates and is left out.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson


def early_result(exp_home: float, exp_away: float, share: float, max_goals: int = 8) -> dict[str, float]:
    """P(home ahead / level / away ahead) after the part of the match holding `share` of its goals."""
    g = np.arange(max_goals + 1)
    grid = np.outer(poisson.pmf(g, exp_home * share), poisson.pmf(g, exp_away * share))
    grid /= grid.sum()
    i, j = np.indices(grid.shape)
    return {"home": float(grid[i > j].sum()), "draw": float(grid[i == j].sum()),
            "away": float(grid[i < j].sum()), "no_goal": float(grid[0, 0])}
