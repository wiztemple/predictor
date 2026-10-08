"""Gradient-boosted stacking model over base-model outputs and form features.

Trained walk-forward: for each period, fit only on rows dated before the period.
Base-model features must themselves be out-of-sample (walk-forward) predictions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from predictor.metrics import OUTCOME_INDEX

BASE_FEATURES = [
    "elo_diff", "elo_p_home", "elo_p_draw", "elo_p_away",
    "dc_p_home", "dc_p_draw", "dc_p_away", "dc_exp_home_goals", "dc_exp_away_goals",
    "home_form_pts", "away_form_pts", "home_form_gd", "away_form_gd",
    "home_rest_days", "away_rest_days", "home_n_prev", "away_n_prev",
]
ODDS_FEATURES = ["bk_p_home", "bk_p_draw", "bk_p_away"]

# Fixed in advance (not tuned on the test period): shallow trees, strong regularisation.
GBM_PARAMS = dict(
    max_depth=3, learning_rate=0.04, max_iter=400, l2_regularization=1.0, min_samples_leaf=40,
    early_stopping=True, validation_fraction=0.2, n_iter_no_change=30, random_state=0,
)


def walk_forward_gbm(table: pd.DataFrame, features: list[str], test_mask: pd.Series,
                     train_mask: pd.Series, freq: str = "M") -> pd.DataFrame:
    """Returns p_home/p_draw/p_away for test rows (index preserved)."""
    y_all = table["outcome"].map(OUTCOME_INDEX)
    test = table[test_mask]
    out = []
    for period, rows in test.groupby(test["date"].dt.to_period(freq), sort=True):
        train = table[train_mask & (table["date"] < period.start_time)]
        model = HistGradientBoostingClassifier(**GBM_PARAMS).fit(train[features], y_all[train.index])
        p = model.predict_proba(rows[features])
        probs = np.zeros((len(rows), 3))
        probs[:, model.classes_] = p
        out.append(pd.DataFrame(probs, index=rows.index, columns=["p_home", "p_draw", "p_away"]))
    return pd.concat(out)
