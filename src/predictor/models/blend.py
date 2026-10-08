"""Weighted average of Elo and Dixon-Coles home/draw/away probabilities.

The weight is chosen on pre-test seasons (scripts/backtest.py). Goals markets
and the scoreline grid come from Dixon-Coles unchanged, since Elo has no goals
model - so the grid's implied 1X2 differs slightly from the blended 1X2.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from predictor.config import load_config
from predictor.models.base import EXTRA_COLUMNS, PREDICTION_COLUMNS, MatchModel
from predictor.models.dixon_coles import DixonColesModel
from predictor.models.elo import EloModel

P = ["p_home", "p_draw", "p_away"]


class BlendModel(MatchModel):
    name = "blend"
    version = "1.0"

    def __init__(self, weight_elo: float | None = None, **_: Any) -> None:
        cfg = load_config()["models"]["blend"]
        self.weight_elo = cfg["weight_elo"] if weight_elo is None else weight_elo
        self.elo = EloModel()
        self.dc = DixonColesModel()

    def _fit(self, matches: pd.DataFrame) -> None:
        self.elo.fit(matches, as_of=self.as_of)
        self.dc.fit(matches, as_of=self.as_of)

    def _predict(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        e = self.elo.predict(fixtures)
        d = self.dc.predict(fixtures)
        w = self.weight_elo
        out = d.copy()
        out[P] = w * e[P].to_numpy() + (1 - w) * d[P].to_numpy()
        return out[PREDICTION_COLUMNS + EXTRA_COLUMNS]

    def grid(self, league: str, home: str, away: str):
        return self.dc.grid(league, home, away)
