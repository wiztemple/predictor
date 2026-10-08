"""Load football-data.co.uk "extra leagues" files (new/{CODE}.csv) into the shared schema.

These hold every season in one file, with columns Country, League, Season
('2019/2020'), Date, Time, Home, Away, HG, AG, Res and closing odds only
(no opening odds, no over/under odds).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from predictor.loaders.football_data import AH_COLUMNS, OU_COLUMNS, parse_dates, read_raw_csv, select_odds
from predictor.schema import MATCH_COLUMNS, outcome_from_scores

log = logging.getLogger(__name__)


def season_from_extra(s: pd.Series) -> pd.Series:
    """'2019/2020' -> '2019-20'. Calendar-year seasons ('2020') are not supported."""
    start = s.str.slice(0, 4)
    bad = ~s.str.match(r"^\d{4}/\d{4}$")
    if bad.any():
        raise ValueError(f"unsupported season labels (calendar-year league?): {sorted(s[bad].unique())[:5]}")
    return start + "-" + (start.astype(int) + 1).mod(100).astype(str).str.zfill(2)


def clean_extra(raw: pd.DataFrame, code: str, country: str, league: str, priority, first_season: str) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(columns=MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS)
    raw = raw[(raw["Country"].str.strip() == country) & (raw["League"].str.strip() == league)]
    df = pd.DataFrame({
        "sport": "football",
        "league": code,
        "season": season_from_extra(raw["Season"].str.strip()),
        "date": parse_dates(raw["Date"]),
        "home": raw["Home"].str.strip(),
        "away": raw["Away"].str.strip(),
        "home_score": pd.to_numeric(raw["HG"], errors="coerce"),
        "away_score": pd.to_numeric(raw["AG"], errors="coerce"),
    })
    df = pd.concat([df, select_odds(raw, priority)], axis=1)
    df["odds_over_2_5"] = np.nan
    df["odds_under_2_5"] = np.nan
    df["ou_source"] = None
    for c in AH_COLUMNS[:3]:
        df[c] = np.nan  # no Asian handicap odds in the extra-leagues files
    df["ah_source"] = None
    keep = (df["season"] >= first_season) & df["date"].notna() & df["home_score"].notna() & df["away_score"].notna()
    keep &= (df["home"] != "") & (df["away"] != "")
    df = df[keep].copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["outcome"] = outcome_from_scores(df["home_score"], df["away_score"])
    return df[MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS]


def load_extra_leagues(raw_dir: Path, extra: dict, priority, first_season: str, wanted=None) -> list[pd.DataFrame]:
    frames = []
    for code, meta in extra.items():
        if wanted is not None and code not in wanted:
            continue
        path = Path(raw_dir) / "extra" / f"{code}.csv"
        if not path.exists():
            log.warning("extra league %s: %s missing (run download_data.py)", code, path)
            continue
        frames.append(clean_extra(read_raw_csv(path), code, meta["country"], meta["league"], priority, first_season))
    return frames
