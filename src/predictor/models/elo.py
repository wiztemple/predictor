"""Football Elo model: Elo ratings + per-league ordered-logit draw model."""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from predictor.config import load_config, season_of
from predictor.models.base import PREDICTION_COLUMNS, MatchModel
from predictor.models.ordered_logit import AWAY, DRAW, HOME, OrderedLogit
from predictor.ratings.elo import EloRatings

log = logging.getLogger(__name__)

_Y = {"A": AWAY, "D": DRAW, "H": HOME}
_SCORE = {"A": 0.0, "D": 0.5, "H": 1.0}
MIN_LEAGUE_RECORDS = 300


def goal_diff_multiplier(gd: int) -> float:
    """World Football Elo margin-of-victory weight: 1, 1, 1.5, then (11+|gd|)/8."""
    gd = abs(int(gd))
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11.0 + gd) / 8.0


def _key(league: str, team: str) -> str:
    return f"{league}:{team}"


class EloModel(MatchModel):
    name = "elo"
    version = "1.0"

    def __init__(self, **overrides: Any) -> None:
        p = {**load_config()["models"]["elo"], **overrides}
        self.params = p
        # lower league -> the league above it (to recognise relegated clubs)
        self.parent = p.get("tiers") or load_config()["football_data"].get("tiers", {})
        self._reset()

    def _reset(self) -> None:
        p = self.params
        self.elo = EloRatings(
            k=p["k"], home_advantage=p["home_advantage"], initial=p["initial_rating"], scale=p["scale"]
        )
        self._season: dict[str, str] = {}
        self._season_teams: dict[str, set[str]] = {}
        self._prev_teams: dict[str, set[str]] = {}
        self._first_date: dict[str, pd.Timestamp] = {}
        self._records: list[tuple[str, pd.Timestamp, float, int]] = []
        self._n_done = 0
        self._last_row: tuple | None = None
        self.draw_models: dict[str, OrderedLogit] = {}
        self.pooled = OrderedLogit()

    # ---- rating bookkeeping -------------------------------------------------
    def _mean(self, keys) -> float:
        return float(np.mean([self.elo.get(k) for k in keys]))

    def _came_down(self, league: str, team: str) -> bool:
        """True if `team` played in the league above `league` this or last season (relegated)."""
        parent = self.parent.get(league)
        if not parent:
            return False
        k = _key(parent, team)
        return k in self._season_teams.get(parent, set()) or k in self._prev_teams.get(parent, set())

    def _start_rating(self, league: str, team: str, base: float | None) -> float:
        """Starting rating for a team new to `league`: league mean plus an offset that is
        negative for promoted clubs and positive for clubs relegated from the league above."""
        if base is None:  # first season in the data: no reference, everyone starts equal
            return self.elo.initial
        off = self.params["relegated_offset"] if self._came_down(league, team) else self.params["new_team_offset"]
        return base + off

    def _new_team_rating(self, league: str, team: str) -> float:
        ref = self._prev_teams.get(league)
        return self._start_rating(league, team, self._mean(ref) if ref else None)

    def _regressed(self, keys) -> dict[str, float]:
        m = self._mean(keys)
        r = self.params["season_regression"]
        return {k: self.elo.get(k) + r * (m - self.elo.get(k)) for k in keys}

    def _start_season(self, league: str, season: str) -> None:
        prev = self._season_teams.get(league)
        if prev:
            for k, v in self._regressed(prev).items():
                self.elo.set(k, v)
            self._prev_teams[league] = prev
        self._season[league] = season
        self._season_teams[league] = set()

    # ---- fitting ---------------------------------------------------------------
    def _is_continuation(self, matches: pd.DataFrame) -> bool:
        n = self._n_done
        if n == 0 or len(matches) < n:
            return False
        r = matches.iloc[n - 1]
        return (r["date"], r["league"], r["home"], r["away"]) == self._last_row

    def _fit(self, matches: pd.DataFrame) -> None:
        if not self._is_continuation(matches):
            self._reset()
        new = matches.iloc[self._n_done:]
        for league, season, date, home, away, hs, as_, outcome in new[
            ["league", "season", "date", "home", "away", "home_score", "away_score", "outcome"]
        ].itertuples(index=False):
            if self._season.get(league) != season:
                self._start_season(league, season)
            self._first_date.setdefault(league, date)
            hk, ak = _key(league, home), _key(league, away)
            for team, k in ((home, hk), (away, ak)):
                if k not in self.elo.ratings:
                    self.elo.set(k, self._new_team_rating(league, team))
                self._season_teams[league].add(k)
            diff = self.elo.update(hk, ak, _SCORE[outcome], goal_diff_multiplier(hs - as_))
            self._records.append((league, date, diff, _Y[outcome]))
        self._n_done = len(matches)
        last = matches.iloc[-1]
        self._last_row = (last["date"], last["league"], last["home"], last["away"])
        self._fit_draw_models()

    def _fit_draw_models(self) -> None:
        rec = pd.DataFrame(self._records, columns=["league", "date", "diff", "y"])
        burn = pd.Timedelta(days=self.params["burn_in_days"])
        rec = rec[rec["date"] >= rec["league"].map(self._first_date) + burn]
        if len(rec) < MIN_LEAGUE_RECORDS:
            rec = pd.DataFrame(self._records, columns=["league", "date", "diff", "y"])
        x_scale = self.params["scale"] / 4.0  # keeps x ~ O(1) for the optimiser
        self.pooled.fit(rec["diff"].to_numpy() / x_scale, rec["y"].to_numpy())
        for league, g in rec.groupby("league"):
            if len(g) < MIN_LEAGUE_RECORDS:
                continue
            m = self.draw_models.get(league)
            if m is None:
                m = OrderedLogit()
                m.params = self.pooled.params.copy()
            self.draw_models[league] = m.fit(g["diff"].to_numpy() / x_scale, g["y"].to_numpy())

    # ---- prediction ------------------------------------------------------------
    def _rating_view(self, league: str, season: str) -> tuple[dict[str, float], float | None]:
        """Ratings as they stand for a fixture in `season` (applies pending season regression),
        plus the league mean that new teams' starting ratings are based on (None = no reference)."""
        if self._season.get(league) == season or not self._season_teams.get(league):
            ref = self._prev_teams.get(league)
            return self.elo.ratings, (self._mean(ref) if ref else None)
        current = self._season_teams[league]
        view = {**self.elo.ratings, **self._regressed(current)}
        return view, float(np.mean([view[k] for k in current]))

    def rating_diffs(self, fixtures: pd.DataFrame) -> np.ndarray:
        diffs = np.empty(len(fixtures))
        unknown = set()
        for i, (league, date, home, away) in enumerate(
            fixtures[["league", "date", "home", "away"]].itertuples(index=False)
        ):
            view, base = self._rating_view(league, season_of(pd.Timestamp(date), league=league))
            hk, ak = _key(league, home), _key(league, away)
            unknown |= {k for k in (hk, ak) if k not in view}
            rh = view[hk] if hk in view else self._start_rating(league, home, base)
            ra = view[ak] if ak in view else self._start_rating(league, away, base)
            diffs[i] = rh + self.elo.home_advantage - ra
        if unknown:
            log.warning("elo: no rating for %s; using new-team rating", sorted(unknown))
        return diffs

    def _predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        diffs = self.rating_diffs(fixtures)
        x = diffs / (self.params["scale"] / 4.0)
        probs = np.empty((len(fixtures), 3))
        for league in fixtures["league"].unique():
            idx = (fixtures["league"] == league).to_numpy()
            probs[idx] = self.draw_models.get(league, self.pooled).predict_proba(x[idx])
        out = fixtures[["league", "date", "home", "away"]].copy()
        out["p_home"], out["p_draw"], out["p_away"] = probs[:, HOME], probs[:, DRAW], probs[:, AWAY]
        out["elo_diff"] = diffs
        return out[PREDICTION_COLUMNS + ["elo_diff"]]

    def ratings_table(self, league: str) -> pd.DataFrame:
        teams = self._season_teams.get(league, set())
        rows = [(k.split(":", 1)[1], self.elo.get(k)) for k in teams]
        return pd.DataFrame(rows, columns=["team", "rating"]).sort_values("rating", ascending=False)
