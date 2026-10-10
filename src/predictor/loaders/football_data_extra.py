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

from predictor.loaders.football_data import AH_COLUMNS, CORNER_COLUMNS, HT_COLUMNS, OU_COLUMNS, parse_dates, read_raw_csv, select_odds
from predictor.schema import MATCH_COLUMNS, outcome_from_scores

log = logging.getLogger(__name__)


def season_from_extra(s: pd.Series, calendar_year: bool = False) -> pd.Series:
    """'2019/2020' -> '2019-20'; for a calendar-year league, '2020' -> '2020-21' (see config.season_of)."""
    start = s.str.slice(0, 4)
    pattern = r"^\d{4}$" if calendar_year else r"^\d{4}/\d{4}$"
    bad = ~s.str.match(pattern)
    if bad.any():
        raise ValueError(f"unexpected season labels (calendar_year={calendar_year}): {sorted(s[bad].unique())[:5]}")
    return start + "-" + (start.astype(int) + 1).mod(100).astype(str).str.zfill(2)


def clean_extra(raw: pd.DataFrame, code: str, country: str, league: str, priority, first_season: str,
                calendar_year: bool = False) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame(columns=MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS + HT_COLUMNS + CORNER_COLUMNS)
    raw = raw[(raw["Country"].str.strip() == country) & (raw["League"].str.strip() == league)]
    df = pd.DataFrame({
        "sport": "football",
        "league": code,
        "season": season_from_extra(raw["Season"].astype(str).str.strip(), calendar_year),
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
    df["ht_home_score"] = np.nan  # extra-leagues files have no half-time scores
    df["ht_away_score"] = np.nan
    for c in CORNER_COLUMNS:
        df[c] = np.nan  # ...nor corners
    keep = (df["season"] >= first_season) & df["date"].notna() & df["home_score"].notna() & df["away_score"].notna()
    keep &= (df["home"] != "") & (df["away"] != "")
    df = df[keep].copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["outcome"] = outcome_from_scores(df["home_score"], df["away_score"])
    return df[MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS + HT_COLUMNS + CORNER_COLUMNS]


def load_extra_leagues(raw_dir: Path, extra: dict, priority, first_season: str, wanted=None) -> list[pd.DataFrame]:
    from predictor.config import calendar_year_leagues

    calendar = calendar_year_leagues()
    frames = []
    for code, meta in extra.items():
        if wanted is not None and code not in wanted:
            continue
        path = Path(raw_dir) / "extra" / f"{code}.csv"
        if not path.exists():
            log.warning("extra league %s: %s missing (run download_data.py)", code, path)
            continue
        frames.append(clean_extra(read_raw_csv(path), code, meta["country"], meta["league"], priority, first_season,
                                  calendar_year=code in calendar))
    return frames
