"""Shared, sport-agnostic match table schema.

Every sport loader must return a DataFrame with MATCH_COLUMNS. Sports without
draws (tennis, basketball) simply never produce outcome 'D' and leave
odds_draw empty.
"""
from __future__ import annotations

import pandas as pd

MATCH_COLUMNS = [
    "sport",
    "league",
    "season",
    "date",
    "home",
    "away",
    "home_score",
    "away_score",
    "outcome",
    "odds_home",
    "odds_draw",
    "odds_away",
]

# Optional columns a loader may add after the required ones.
# (odds_over/under_2_5 are football-specific goals-market odds.)
OPTIONAL_COLUMNS = ["odds_source", "odds_over_2_5", "odds_under_2_5", "ou_source",
                    "ah_line", "odds_ah_home", "odds_ah_away", "ah_source", "ht_home_score", "ht_away_score",
                    "home_corners", "away_corners"]

OUTCOMES = ("H", "D", "A")


def outcome_from_scores(home_score: pd.Series, away_score: pd.Series) -> pd.Series:
    out = pd.Series("D", index=home_score.index, dtype=object)
    out[home_score > away_score] = "H"
    out[home_score < away_score] = "A"
    return out


def validate_matches(df: pd.DataFrame) -> None:
    """Raise ValueError if df does not satisfy the shared schema."""
    missing = [c for c in MATCH_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    if df[["sport", "league", "season", "date", "home", "away"]].isna().any().any():
        raise ValueError("null values in key columns")
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise ValueError("date must be datetime64")
    bad = ~df["outcome"].isin(OUTCOMES)
    if bad.any():
        raise ValueError(f"{bad.sum()} rows with invalid outcome")
    if not (outcome_from_scores(df["home_score"], df["away_score"]) == df["outcome"]).all():
        raise ValueError("outcome inconsistent with scores")
    if df.duplicated(["league", "date", "home", "away"]).any():
        raise ValueError("duplicate matches")
