"""Walk-forward evaluation: for each period, fit on data before it, predict it."""
from __future__ import annotations

from typing import Callable

import pandas as pd

from predictor.models.base import MatchModel


def walk_forward(
    model: MatchModel | Callable[[], MatchModel],
    matches: pd.DataFrame,
    test_mask: pd.Series,
    freq: str = "W-MON",
) -> pd.DataFrame:
    """Predict every match in `test_mask`, refitting at the start of each period.

    A period with freq 'W-MON' runs Tuesday 00:00 to Monday 23:59; the model is
    fitted on matches strictly before the period's first day. Passing a model
    instance (not a factory) lets models reuse state between refits (Elo does
    this incrementally, Dixon-Coles warm-starts) - the cutoff still guarantees
    no future data is used.

    Returns the predictions joined with actual outcome, scores and odds.
    """
    test = matches[test_mask]
    periods = test["date"].dt.to_period(freq)
    out = []
    for period, fixtures in test.groupby(periods, sort=True):
        cutoff = period.start_time
        m = model() if callable(model) and not isinstance(model, MatchModel) else model
        m.fit(matches, as_of=cutoff)
        pred = m.predict(fixtures[["league", "date", "home", "away"]])
        actual = fixtures[["home_score", "away_score", "outcome", "season",
                           "odds_home", "odds_draw", "odds_away"]].reset_index(drop=True)
        pred = pd.concat([pred.reset_index(drop=True), actual], axis=1)
        pred["cutoff"] = cutoff
        pred["match_idx"] = fixtures.index.to_numpy()
        out.append(pred)
    return pd.concat(out, ignore_index=True)
