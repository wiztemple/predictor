"""Total-corners model: per-league team corner ratings, negative binomial match totals.

    log E[home corners] = c + home + won[h] + conceded[a]
    log E[away corners] = c        + won[a] + conceded[h]

Fitted per league by weighted Poisson likelihood with exponential time decay and
a ridge penalty (same scheme as Dixon-Coles). Home and away corners are
negatively correlated (the side on top takes most of them), so the match total
is modelled directly: NB(mean = sum of both sides, dispersion k). k and the fit
settings are chosen on the tune seasons by scripts/backtest_corners.py.

Leagues without corner data (the football-data "extra" leagues) get no output.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import nbinom, poisson

from predictor.models.base import LeakageError

CORNER_LINES = (7.5, 8.5, 9.5, 10.5, 11.5)
MIN_LEAGUE_MATCHES = 100


def line_key(line: float) -> str:
    return f"over_{line:g}".replace(".", "_")


def total_pmf(mean: np.ndarray, k: float | None, max_corners: int = 40) -> np.ndarray:
    """P(total = 0..max_corners) per match; k=None (or inf) is Poisson."""
    x = np.arange(max_corners + 1)
    mean = np.asarray(mean, float)[:, None]
    if not k or np.isinf(k):
        return poisson.pmf(x, mean)
    return nbinom.pmf(x, k, k / (k + mean))


def over_probs(mean: np.ndarray, k: float | None, lines=CORNER_LINES) -> dict[float, np.ndarray]:
    """P(total > line) for each half-goal line."""
    mean = np.asarray(mean, float)
    out = {}
    for line in lines:
        n = int(np.floor(line))
        if not k or np.isinf(k):
            out[line] = poisson.sf(n, mean)
        else:
            out[line] = nbinom.sf(n, k, k / (k + mean))
    return out


def count_log_lik(mean: np.ndarray, total: np.ndarray, k: float | None) -> np.ndarray:
    total = np.asarray(total)
    if not k or np.isinf(k):
        return poisson.logpmf(total, mean)
    return nbinom.logpmf(total, k, k / (k + np.asarray(mean, float)))


def fit_dispersion(mean: np.ndarray, total: np.ndarray, lo: float = 2.0, hi: float = 2000.0) -> float:
    """Maximum-likelihood NB dispersion k for out-of-sample means (searched on a log grid)."""
    grid = np.exp(np.linspace(np.log(lo), np.log(hi), 200))
    ll = [count_log_lik(mean, total, k).sum() for k in grid]
    return float(grid[int(np.argmax(ll))])


def _nll(theta, hi, ai, x, y, w, n, l2):
    c, home = theta[:2]
    won, con = theta[2:2 + n], theta[2 + n:]
    log_h = c + home + won[hi] + con[ai]
    log_a = c + won[ai] + con[hi]
    mh, ma = np.exp(log_h), np.exp(log_a)
    f = -np.sum(w * (x * log_h - mh + y * log_a - ma)) + l2 * (won @ won + con @ con)
    gh, ga = w * (x - mh), w * (y - ma)
    g = np.empty_like(theta)
    g[0] = -(gh.sum() + ga.sum())
    g[1] = -gh.sum()
    g[2:2 + n] = -(np.bincount(hi, gh, n) + np.bincount(ai, ga, n)) + 2 * l2 * won
    g[2 + n:] = -(np.bincount(ai, gh, n) + np.bincount(hi, ga, n)) + 2 * l2 * con
    return f, g


@dataclass
class _League:
    teams: dict[str, int]
    c: float
    home: float
    won: np.ndarray
    conceded: np.ndarray
    new_won: float
    new_conceded: float

    def means(self, home: str, away: str) -> tuple[float, float]:
        def p(t):
            i = self.teams.get(t)
            return (self.won[i], self.conceded[i]) if i is not None else (self.new_won, self.new_conceded)
        wh, ch = p(home)
        wa, ca = p(away)
        return float(np.exp(self.c + self.home + wh + ca)), float(np.exp(self.c + wa + ch))


class CornersModel:
    name = "corners"
    version = "1"

    def __init__(self, half_life_days: float = 240, l2_penalty: float = 3.0, max_history_days: int = 1100,
                 dispersion_k: float | None = None, new_team_quantile: float = 0.3, lines=CORNER_LINES):
        self.half_life_days = half_life_days
        self.l2 = l2_penalty
        self.max_history_days = max_history_days
        self.k = dispersion_k
        self.q = new_team_quantile
        self.lines = tuple(lines)
        self.leagues: dict[str, _League] = {}
        self.fitted_until: pd.Timestamp | None = None

    @classmethod
    def from_config(cls, cfg: dict) -> "CornersModel":
        c = cfg["models"]["corners"]
        return cls(c["half_life_days"], c["l2_penalty"], c["max_history_days"], c.get("dispersion_k"),
                   c["new_team_quantile"], c.get("lines", CORNER_LINES))

    def fit(self, matches: pd.DataFrame, as_of=None) -> "CornersModel":
        m = matches[matches["home_corners"].notna() & matches["away_corners"].notna()]
        if as_of is not None:
            m = m[m["date"] < pd.Timestamp(as_of)]
        if m.empty:
            raise ValueError("no corner data before cutoff")
        end = m["date"].max()
        self.fitted_until = end
        m = m[m["date"] > end - pd.Timedelta(days=self.max_history_days)]
        xi = np.log(2) / self.half_life_days
        prev, self.leagues = self.leagues, {}
        for lg, d in m.groupby("league"):
            if len(d) < MIN_LEAGUE_MATCHES:
                continue
            self.leagues[lg] = self._fit_league(d, end, xi, prev.get(lg))
        return self

    def _fit_league(self, d: pd.DataFrame, end, xi, warm: _League | None) -> _League:
        teams = sorted(set(d["home"]) | set(d["away"]))
        idx = {t: i for i, t in enumerate(teams)}
        n = len(teams)
        hi = d["home"].map(idx).to_numpy()
        ai = d["away"].map(idx).to_numpy()
        x = d["home_corners"].to_numpy(float)
        y = d["away_corners"].to_numpy(float)
        w = np.exp(-xi * (end - d["date"]).dt.days.to_numpy())
        theta0 = np.zeros(2 + 2 * n)
        theta0[0] = np.log(max((np.sum(w * (x + y)) / (2 * w.sum())), 0.1))
        if warm is not None:  # warm start from last week's fit
            theta0[0], theta0[1] = warm.c, warm.home
            for t, i in idx.items():
                j = warm.teams.get(t)
                if j is not None:
                    theta0[2 + i], theta0[2 + n + i] = warm.won[j], warm.conceded[j]
        r = minimize(_nll, theta0, args=(hi, ai, x, y, w, n, self.l2), jac=True, method="L-BFGS-B")
        th = r.x
        won, con = th[2:2 + n], th[2 + n:]
        return _League(idx, th[0], th[1], won, con,
                       float(np.quantile(won, self.q)), float(np.quantile(con, 1 - self.q)))

    def predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        """league, date, home, away, exp_home_corners, exp_away_corners, exp_corners, p_over_*.
        NaN where the league has no corner model."""
        if self.fitted_until is None:
            raise RuntimeError("corners: call fit() before predict()")
        f = fixtures[["league", "date", "home", "away"]].reset_index(drop=True)
        if len(f) and (pd.to_datetime(f["date"]) <= self.fitted_until).any():
            raise LeakageError(f"corners: fixtures dated on/before last training match {self.fitted_until:%Y-%m-%d}")
        eh = np.full(len(f), np.nan)
        ea = np.full(len(f), np.nan)
        for i, r in f.iterrows():
            lg = self.leagues.get(r["league"])
            if lg is not None:
                eh[i], ea[i] = lg.means(r["home"], r["away"])
        out = f.copy()
        out["exp_home_corners"], out["exp_away_corners"] = eh, ea
        out["exp_corners"] = eh + ea
        ok = ~np.isnan(eh)
        for line, p in over_probs(np.where(ok, eh + ea, 1.0), self.k, self.lines).items():
            out[f"p_{line_key(line)}"] = np.where(ok, p, np.nan)
        return out


class LeagueAverageCorners:
    """Baseline: every match in a league gets that league's mean total over the past `days`."""

    def __init__(self, days: int = 365, dispersion_k: float | None = None, lines=CORNER_LINES):
        self.days, self.k, self.lines = days, dispersion_k, tuple(lines)
        self.means: dict[str, float] = {}
        self.fitted_until = None

    def fit(self, matches: pd.DataFrame, as_of=None) -> "LeagueAverageCorners":
        m = matches[matches["home_corners"].notna() & matches["away_corners"].notna()]
        if as_of is not None:
            m = m[m["date"] < pd.Timestamp(as_of)]
        self.fitted_until = m["date"].max()
        m = m[m["date"] > self.fitted_until - pd.Timedelta(days=self.days)]
        self.means = (m["home_corners"] + m["away_corners"]).groupby(m["league"]).mean().to_dict()
        return self

    def predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        if len(fixtures) and (pd.to_datetime(fixtures["date"]) <= self.fitted_until).any():
            raise LeakageError("corners baseline: fixtures on/before last training match")
        out = fixtures[["league", "date", "home", "away"]].reset_index(drop=True)
        out["exp_corners"] = out["league"].map(self.means).astype(float)
        ok = out["exp_corners"].notna().to_numpy()
        for line, p in over_probs(np.where(ok, out["exp_corners"], 1.0), self.k, self.lines).items():
            out[f"p_{line_key(line)}"] = np.where(ok, p, np.nan)
        return out
