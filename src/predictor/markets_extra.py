"""Extra betting markets, all read from ONE scoreline grid that agrees with the headline numbers.

1. adjust_grid: rescale the Dixon-Coles scoreline grid (iterative proportional fitting) so its
   1X2, over/under 1.5/2.5/3.5 and both-teams-to-score match the published (blended / calibrated)
   numbers. Every market read from it is then consistent with the rest of the site.
2. half_grid: first/second-half goals as independent Poisson (expected goals x share per half),
   with full-time results rescaled to the published 1X2 - for half-time markets and HT/FT.

The same functions price markets live and settle them in the backtest.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson

# ---------------------------------------------------------------- grids


def adjust_grid(grid: np.ndarray, p1x2: tuple[float, float, float], goals: dict[str, float],
                iters: int = 200, tol: float = 1e-9) -> np.ndarray:
    """Iterative proportional fitting of a scoreline grid to target marginals.
    `goals` may hold over_1_5, over_2_5, over_3_5, btts (P of 'yes')."""
    g = np.asarray(grid, float).copy()
    i, j = np.indices(g.shape)
    parts = [([i > j, i == j, i < j], list(p1x2))]
    for key, mask in (("over_1_5", i + j >= 2), ("over_2_5", i + j >= 3), ("over_3_5", i + j >= 4),
                      ("btts", (i >= 1) & (j >= 1))):
        if goals.get(key) is not None:
            parts.append(([mask, ~mask], [goals[key], 1 - goals[key]]))
    for _ in range(iters):
        worst = 0.0
        for masks, targets in parts:
            for m, t in zip(masks, targets):
                s = g[m].sum()
                if s > 0 and t > 0:
                    worst = max(worst, abs(s - t))
                    g[m] *= t / s
        g /= g.sum()
        if worst < tol:
            break
    return g


def half_grid(lam: float, mu: float, share_1h: float, p1x2: tuple[float, float, float] | None = None,
              n: int = 8) -> np.ndarray:
    """P[a, b, c, d]: home/away goals in the 1st half (a, b) and 2nd half (c, d).
    If p1x2 is given, cells are rescaled by full-time outcome to match it."""
    k = np.arange(n)
    h1, a1 = poisson.pmf(k, lam * share_1h), poisson.pmf(k, mu * share_1h)
    h2, a2 = poisson.pmf(k, lam * (1 - share_1h)), poisson.pmf(k, mu * (1 - share_1h))
    P = np.einsum("a,b,c,d->abcd", h1, a1, h2, a2)
    P /= P.sum()
    if p1x2 is not None:
        a, b, c, d = np.indices(P.shape)
        ft_h, ft_a = a + c, b + d
        for m, t in ((ft_h > ft_a, p1x2[0]), (ft_h == ft_a, p1x2[1]), (ft_h < ft_a, p1x2[2])):
            s = P[m].sum()
            if s > 0:
                P[m] *= t / s
        P /= P.sum()
    return P


# ---------------------------------------------------------------- markets


def _res(h, a):
    return np.where(h > a, "1", np.where(h == a, "X", "2"))


def full_time_markets(g: np.ndarray) -> dict[str, dict[str, float]]:
    i, j = np.indices(g.shape)
    tot = i + j
    gg = (i >= 1) & (j >= 1)
    res = _res(i, j)
    over = tot >= 3
    out: dict[str, dict[str, float]] = {}
    out["result_btts"] = {f"{r}&{b}": float(g[(res == r) & (gg if b == "GG" else ~gg)].sum())
                          for r in ("1", "X", "2") for b in ("GG", "NG")}
    out["result_ou25"] = {f"{r}&{o}": float(g[(res == r) & (over if o == "O" else ~over)].sum())
                          for r in ("1", "X", "2") for o in ("O", "U")}
    dc = {"1X": res != "2", "12": res != "X", "X2": res != "1"}
    out["dc_ou25"] = {f"{d}&{o}": float(g[m & (over if o == "O" else ~over)].sum())
                      for d, m in dc.items() for o in ("O", "U")}
    for side, goals in (("home", i), ("away", j)):
        for line, thr in (("0_5", 1), ("1_5", 2)):
            p = float(g[goals >= thr].sum())
            out[f"{side}_ou{line}"] = {"over": p, "under": 1 - p}
    out["clean_sheet"] = {"home": float(g[j == 0].sum()), "away": float(g[i == 0].sum())}
    out["win_to_nil"] = {"home": float(g[(i > j) & (j == 0)].sum()), "away": float(g[(j > i) & (i == 0)].sum())}
    out["exact_goals"] = {str(k): float(g[tot == k].sum()) for k in range(5)}
    out["exact_goals"]["5+"] = float(g[tot >= 5].sum())
    odd = float(g[tot % 2 == 1].sum())
    out["odd_even"] = {"odd": odd, "even": 1 - odd}
    ph, pa = float(g[i > j].sum()), float(g[i < j].sum())
    out["dnb"] = {"1": ph / (ph + pa), "2": pa / (ph + pa)}  # draw = stake back
    return out


def half_time_markets(P: np.ndarray) -> dict[str, dict[str, float]]:
    a, b, c, d = np.indices(P.shape)
    ht, ft = _res(a, b), _res(a + c, b + d)
    out: dict[str, dict[str, float]] = {}
    out["ht_result"] = {r: float(P[ht == r].sum()) for r in ("1", "X", "2")}
    out["htft"] = {f"{x}/{y}": float(P[(ht == x) & (ft == y)].sum()) for x in ("1", "X", "2") for y in ("1", "X", "2")}
    for line, thr in (("0_5", 1), ("1_5", 2)):
        p = float(P[a + b >= thr].sum())
        out[f"ht_ou{line}"] = {"over": p, "under": 1 - p}
    t1, t2 = a + b, c + d
    out["highest_half"] = {"1st": float(P[t1 > t2].sum()), "2nd": float(P[t2 > t1].sum()),
                           "equal": float(P[t1 == t2].sum())}
    return out


def all_markets(lam: float, mu: float, rho: float, p1x2, goals: dict[str, float], share_1h: float,
                max_goals: int = 10) -> tuple[np.ndarray, dict[str, dict[str, float]]]:
    from predictor.models.dixon_coles import score_grid

    g = adjust_grid(score_grid(lam, mu, rho, max_goals), p1x2, goals)
    m = full_time_markets(g)
    m.update(half_time_markets(half_grid(lam, mu, share_1h, p1x2)))
    return g, m


# ---------------------------------------------------------------- settlement (backtest)

def settle(market: str, hs: int, as_: int, hths: float | None = None, htas: float | None = None):
    """Winning outcome key for exclusive markets, or {selection: bool} for yes/no style ones."""
    tot, res = hs + as_, ("1" if hs > as_ else "X" if hs == as_ else "2")
    gg = "GG" if hs >= 1 and as_ >= 1 else "NG"
    if market == "result_btts":
        return f"{res}&{gg}"
    if market == "result_ou25":
        return f"{res}&{'O' if tot >= 3 else 'U'}"
    if market.startswith(("home_ou", "away_ou")):
        goals = hs if market.startswith("home") else as_
        return "over" if goals >= (1 if market.endswith("0_5") else 2) else "under"
    if market == "exact_goals":
        return "5+" if tot >= 5 else str(tot)
    if market == "odd_even":
        return "odd" if tot % 2 else "even"
    if market == "win_to_nil":
        return {"home": hs > as_ and as_ == 0, "away": as_ > hs and hs == 0}
    if hths is None or htas is None or np.isnan(hths) or np.isnan(htas):
        return None
    ht = "1" if hths > htas else "X" if hths == htas else "2"
    if market == "ht_result":
        return ht
    if market == "htft":
        return f"{ht}/{res}"
    if market.startswith("ht_ou"):
        return "over" if hths + htas >= (1 if market.endswith("0_5") else 2) else "under"
    if market == "highest_half":
        t1, t2 = hths + htas, tot - hths - htas
        return "1st" if t1 > t2 else "2nd" if t2 > t1 else "equal"
    raise ValueError(market)


# exclusive markets scored as a single multi-outcome prediction in the backtest
BACKTEST_MARKETS = ["result_btts", "result_ou25", "home_ou0_5", "home_ou1_5", "away_ou0_5", "away_ou1_5",
                    "exact_goals", "odd_even", "ht_result", "htft", "ht_ou0_5", "ht_ou1_5", "highest_half"]
