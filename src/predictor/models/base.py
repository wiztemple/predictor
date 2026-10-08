"""Common model interface.

    model.fit(matches, as_of=cutoff)   # trains only on matches dated before cutoff
    model.predict(fixtures)            # -> PREDICTION_COLUMNS (+ optional extras)

Fixtures need columns league, date, home, away. A model refuses to predict a
fixture dated on or before its last training match, so a leak shows up as an
error rather than as a suspiciously good backtest.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd

# Every model returns these; extra markets are optional columns.
PREDICTION_COLUMNS = ["league", "date", "home", "away", "p_home", "p_draw", "p_away"]
# Goals markets: unders are 1 - over.
EXTRA_COLUMNS = ["exp_home_goals", "exp_away_goals", "p_over_1_5", "p_over_2_5", "p_over_3_5", "p_btts",
                 "top_scorelines", "margin_probs", "lam", "mu", "rho"]


class LeakageError(ValueError):
    pass


class MatchModel(ABC):
    name: str = "base"
    version: str = "0"

    fitted_until: pd.Timestamp | None = None
    as_of: pd.Timestamp | None = None

    def fit(self, matches: pd.DataFrame, as_of: pd.Timestamp | str | None = None) -> "MatchModel":
        if as_of is not None:
            as_of = pd.Timestamp(as_of)
            matches = matches[matches["date"] < as_of]
        if matches.empty:
            raise ValueError("no training matches before cutoff")
        matches = matches.sort_values("date", kind="stable")
        self.fitted_until = matches["date"].max()
        self.as_of = as_of if as_of is not None else self.fitted_until + pd.Timedelta(days=1)
        self._fit(matches)
        return self

    def predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        if self.fitted_until is None:
            raise RuntimeError(f"{self.name}: call fit() before predict()")
        if len(fixtures) and (pd.to_datetime(fixtures["date"]) <= self.fitted_until).any():
            raise LeakageError(
                f"{self.name}: fixtures dated on/before last training match {self.fitted_until:%Y-%m-%d}"
            )
        out = self._predict(fixtures.reset_index(drop=True))
        total = out[["p_home", "p_draw", "p_away"]].sum(axis=1)
        if not ((total - 1).abs() < 1e-6).all():
            raise AssertionError(f"{self.name}: probabilities do not sum to 1")
        return out

    @abstractmethod
    def _fit(self, matches: pd.DataFrame) -> None: ...

    @abstractmethod
    def _predict(self, fixtures: pd.DataFrame) -> pd.DataFrame: ...

    def describe(self) -> str:
        return f"{self.name} v{self.version}"
