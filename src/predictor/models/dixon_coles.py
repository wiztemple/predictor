"""Dixon-Coles (1997) bivariate Poisson model with low-score correction and time decay.

    log lambda_home = mu + home + attack[h] + defence[a]
    log lambda_away = mu        + attack[a] + defence[h]

`defence` is defensive weakness (higher = concedes more). Match weights decay
as exp(-xi * age) with xi = ln 2 / half_life_days. A ridge penalty on
attack/defence fixes identifiability (mu absorbs the mean) and shrinks teams
with little data toward average. Fitted separately per league.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from predictor.config import load_config
from predictor.models.base import EXTRA_COLUMNS, PREDICTION_COLUMNS, MatchModel

log = logging.getLogger(__name__)


def tau(x, y, lam, mu, rho):
    """Dixon-Coles dependence correction for scorelines (x, y)."""
    x, y = np.asarray(x), np.asarray(y)
    t = np.ones(np.broadcast(x, y, lam, mu).shape)
    t = np.where((x == 0) & (y == 0), 1 - lam * mu * rho, t)
    t = np.where((x == 0) & (y == 1), 1 + lam * rho, t)
    t = np.where((x == 1) & (y == 0), 1 + mu * rho, t)
    t = np.where((x == 1) & (y == 1), 1 - rho, t)
    return t


def neg_log_lik(theta, hi, ai, x, y, w, n_teams, l2):
    """Weighted negative log-likelihood and its gradient.

    theta = [mu, home, rho, attack(n), defence(n)].
    """
    mu0, home, rho = theta[:3]
    att = theta[3:3 + n_teams]
    dfn = theta[3 + n_teams:]
    log_l = mu0 + home + att[hi] + dfn[ai]
    log_m = mu0 + att[ai] + dfn[hi]
    lam, mu = np.exp(log_l), np.exp(log_m)

    z00 = (x == 0) & (y == 0)
    z01 = (x == 0) & (y == 1)
    z10 = (x == 1) & (y == 0)
    z11 = (x == 1) & (y == 1)
    t = np.ones_like(lam)
    t[z00] = 1 - lam[z00] * mu[z00] * rho
    t[z01] = 1 + lam[z01] * rho
    t[z10] = 1 + mu[z10] * rho
    t[z11] = 1 - rho
    t = np.maximum(t, 1e-10)

    ll = np.log(t) + x * log_l - lam + y * log_m - mu
    f = -np.sum(w * ll) + l2 * (att @ att + dfn @ dfn)

    # d ll / d log_lambda, d log_mu, d rho
    g_l = x - lam
    g_m = y - mu
    g_r = np.zeros_like(lam)
    g_l[z00] -= lam[z00] * mu[z00] * rho / t[z00]
    g_m[z00] -= lam[z00] * mu[z00] * rho / t[z00]
    g_r[z00] = -lam[z00] * mu[z00] / t[z00]
    g_l[z01] += lam[z01] * rho / t[z01]
    g_r[z01] = lam[z01] / t[z01]
    g_m[z10] += mu[z10] * rho / t[z10]
    g_r[z10] = mu[z10] / t[z10]
    g_r[z11] = -1 / t[z11]

    wl, wm = w * g_l, w * g_m
    grad = np.empty_like(theta)
    grad[0] = -(wl.sum() + wm.sum())
    grad[1] = -wl.sum()
    grad[2] = -np.sum(w * g_r)
    grad[3:3 + n_teams] = -(np.bincount(hi, wl, n_teams) + np.bincount(ai, wm, n_teams)) + 2 * l2 * att
    grad[3 + n_teams:] = -(np.bincount(ai, wl, n_teams) + np.bincount(hi, wm, n_teams)) + 2 * l2 * dfn
    return f, grad


@dataclass
class LeagueFit:
    teams: list[str]
    mu: float
    home: float
    rho: float
    attack: np.ndarray
    defence: np.ndarray
    new_attack: float
    new_defence: float
    # prior for a club relegated from the league above (strong for this league)
    down_attack: float = 0.0
    down_defence: float = 0.0
    relegated: frozenset = frozenset()

    def team_params(self, team: str) -> tuple[float, float, bool]:
        try:
            i = self.teams.index(team)
            return self.attack[i], self.defence[i], True
        except ValueError:
            if team in self.relegated:
                return self.down_attack, self.down_defence, False
            return self.new_attack, self.new_defence, False

    def rates(self, home: str, away: str) -> tuple[float, float, bool]:
        ah, dh, kh = self.team_params(home)
        aa, da, ka = self.team_params(away)
        lam = np.exp(self.mu + self.home + ah + da)
        mu = np.exp(self.mu + aa + dh)
        return lam, mu, kh and ka


def score_grid(lam: float, mu: float, rho: float, max_goals: int) -> np.ndarray:
    """P[i, j] = P(home scores i, away scores j), i, j in 0..max_goals, normalised."""
    g = np.arange(max_goals + 1)
    p = np.outer(poisson.pmf(g, lam), poisson.pmf(g, mu))
    p[:2, :2] *= tau(g[:2, None], g[None, :2], lam, mu, rho)
    return p / p.sum()


def markets_from_grid(grid: np.ndarray, top_n: int = 5) -> dict[str, Any]:
    i, j = np.indices(grid.shape)
    flat = np.argsort(grid, axis=None)[::-1][:top_n]
    return {
        "p_home": grid[i > j].sum(),
        "p_draw": grid[i == j].sum(),
        "p_away": grid[i < j].sum(),
        "exp_home_goals": (i * grid).sum(),
        "exp_away_goals": (j * grid).sum(),
        "p_over_1_5": grid[i + j >= 2].sum(),
        "p_over_2_5": grid[i + j >= 3].sum(),
        "p_over_3_5": grid[i + j >= 4].sum(),
        "p_btts": grid[(i >= 1) & (j >= 1)].sum(),
        "top_scorelines": [
            {"home": int(a), "away": int(b), "p": float(grid[a, b])}
            for a, b in zip(*np.unravel_index(flat, grid.shape))
        ],
    }


class DixonColesModel(MatchModel):
    name = "dixon_coles"
    version = "1.0"

    def __init__(self, **overrides: Any) -> None:
        self.params = {**load_config()["models"]["dixon_coles"], **overrides}
        self.parent = self.params.get("tiers") or load_config()["football_data"].get("tiers", {})
        self.leagues: dict[str, LeagueFit] = {}

    def _fit(self, matches: pd.DataFrame) -> None:
        p = self.params
        start = self.as_of - pd.Timedelta(days=p["max_history_days"])
        recent = matches[matches["date"] >= start]
        previous = self.leagues
        self.leagues = {}
        # clubs seen in each league over the last ~season (to spot relegations)
        last_year = matches[matches["date"] >= self.as_of - pd.Timedelta(days=400)]
        seen = {lg: set(g["home"]) | set(g["away"]) for lg, g in last_year.groupby("league")}
        for league, g in recent.groupby("league"):
            fit = self._fit_league(g, previous.get(league))
            parent = self.parent.get(league)
            if parent:
                fit.relegated = frozenset(seen.get(parent, set()) - set(fit.teams))
            self.leagues[league] = fit

    def _fit_league(self, g: pd.DataFrame, warm: LeagueFit | None) -> LeagueFit:
        p = self.params
        teams = sorted(set(g["home"]) | set(g["away"]))
        n = len(teams)
        idx = {t: i for i, t in enumerate(teams)}
        hi = g["home"].map(idx).to_numpy()
        ai = g["away"].map(idx).to_numpy()
        x = g["home_score"].to_numpy(float)
        y = g["away_score"].to_numpy(float)
        age = (self.as_of - g["date"]).dt.days.to_numpy(float)
        w = np.exp(-np.log(2) / p["half_life_days"] * age)

        theta0 = np.zeros(3 + 2 * n)
        theta0[0], theta0[1], theta0[2] = np.log(max((x.mean() + y.mean()) / 2, 0.1)), 0.25, -0.05
        if warm is not None:
            theta0[:3] = warm.mu, warm.home, warm.rho
            for t, i in idx.items():
                a, d, known = warm.team_params(t)
                if known:
                    theta0[3 + i], theta0[3 + n + i] = a, d
        bounds = [(None, None), (None, None), tuple(p["rho_bounds"])] + [(None, None)] * (2 * n)
        res = minimize(
            neg_log_lik, theta0, args=(hi, ai, x, y, w, n, p["l2_penalty"]),
            jac=True, method="L-BFGS-B", bounds=bounds,
        )
        if not res.success:
            log.warning("dixon_coles %s: optimiser did not converge: %s", g["league"].iat[0], res.message)
        th = res.x
        att, dfn = th[3:3 + n], th[3 + n:]
        q = p["new_team_quantile"]
        return LeagueFit(
            teams=teams, mu=th[0], home=th[1], rho=th[2], attack=att, defence=dfn,
            new_attack=float(np.quantile(att, q)), new_defence=float(np.quantile(dfn, 1 - q)),
            down_attack=float(np.quantile(att, 1 - q)), down_defence=float(np.quantile(dfn, q)),
        )

    def grid(self, league: str, home: str, away: str) -> np.ndarray:
        lf = self.leagues[league]
        lam, mu, _ = lf.rates(home, away)
        return score_grid(lam, mu, lf.rho, self.params["max_goals"])

    def _predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        rows, unknown = [], set()
        for league, home, away in fixtures[["league", "home", "away"]].itertuples(index=False):
            lf = self.leagues.get(league)
            if lf is None:
                raise KeyError(f"dixon_coles: league {league} not in training data")
            lam, mu, known = lf.rates(home, away)
            if not known:
                unknown |= {t for t in (home, away) if t not in lf.teams}
            rows.append(markets_from_grid(score_grid(lam, mu, lf.rho, self.params["max_goals"]),
                                          self.params["top_scorelines"]))
        if unknown:
            log.warning("dixon_coles: no history for %s; using new-team strengths", sorted(unknown))
        out = pd.concat([fixtures[["league", "date", "home", "away"]], pd.DataFrame(rows)], axis=1)
        return out[PREDICTION_COLUMNS + EXTRA_COLUMNS]

    def team_table(self, league: str) -> pd.DataFrame:
        lf = self.leagues[league]
        return pd.DataFrame(
            {"team": lf.teams, "attack": lf.attack, "defence": lf.defence}
        ).assign(net=lambda d: d.attack - d.defence).sort_values("net", ascending=False)
