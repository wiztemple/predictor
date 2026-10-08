"""Load football-data.co.uk CSVs into the shared match schema."""
from __future__ import annotations

import csv
import io
import logging
import re
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from predictor.config import load_config, project_path, season_label
from predictor.schema import MATCH_COLUMNS, outcome_from_scores, validate_matches

log = logging.getLogger(__name__)

FILE_RE = re.compile(r"^(?P<league>[A-Z0-9]+)_(?P<season>\d{4})\.csv$")
_LONG_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
_SHORT_DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2}$")


def read_raw_csv(path: Path) -> pd.DataFrame:
    """Read one file as strings, tolerating BOMs, latin-1 and ragged rows.

    Some files have trailing commas or more fields than the header; rows are
    truncated/padded to the header width rather than skipped.
    """
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return pd.DataFrame()
    header = [h.strip().lstrip("﻿").lstrip("ï»¿") for h in rows[0]]
    while header and header[-1] == "":
        header.pop()
    width = len(header)
    body = [(r + [""] * width)[:width] for r in rows[1:]]
    df = pd.DataFrame(body, columns=header, dtype=object)
    df = df.loc[:, ~df.columns.duplicated()]
    return df.apply(lambda c: c.str.strip())


def parse_dates(s: pd.Series) -> pd.Series:
    """Parse dd/mm/yy and dd/mm/yyyy, which may be mixed in one column."""
    s = s.fillna("").astype(str).str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    long_mask = s.str.match(_LONG_DATE)
    short_mask = s.str.match(_SHORT_DATE)
    out[long_mask] = pd.to_datetime(s[long_mask], format="%d/%m/%Y", errors="coerce")
    out[short_mask] = pd.to_datetime(s[short_mask], format="%d/%m/%y", errors="coerce")
    return out


def select_prices(df: pd.DataFrame, priority: Sequence[Sequence[str]], out_cols: Sequence[str],
                  source_col: str) -> pd.DataFrame:
    """Per row, take the first complete set of decimal odds in priority order.

    `priority` items are [source_name, col_1, ..., col_k] with k == len(out_cols).
    Prices <= 1.0 count as missing.
    """
    n, k = len(df), len(out_cols)
    odds = np.full((n, k), np.nan)
    source = np.full(n, None, dtype=object)
    unfilled = np.ones(n, dtype=bool)
    for name, *cols in priority:
        if len(cols) != k or not all(c in df.columns for c in cols):
            continue
        prices = df[cols].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
        ok = unfilled & (prices > 1.0).all(axis=1)
        odds[ok] = prices[ok]
        source[ok] = name
        unfilled &= ~ok
    out = pd.DataFrame(odds, columns=list(out_cols), index=df.index)
    out[source_col] = source
    return out


def select_odds(df: pd.DataFrame, priority: Sequence[Sequence[str]]) -> pd.DataFrame:
    """1X2 odds: columns odds_home, odds_draw, odds_away, odds_source."""
    return select_prices(df, priority, ["odds_home", "odds_draw", "odds_away"], "odds_source")


OU_COLUMNS = ["odds_over_2_5", "odds_under_2_5", "ou_source"]


AH_COLUMNS = ["ah_line", "odds_ah_home", "odds_ah_away", "ah_source"]
HT_COLUMNS = ["ht_home_score", "ht_away_score"]


def select_ah_odds(df: pd.DataFrame, priority: Sequence[Sequence[str]], line_col: str = "AHCh") -> pd.DataFrame:
    """Closing Asian handicap: the market's closing home line plus a pair of odds at that line.
    Odds without a line (or a line without odds) are dropped together."""
    out = select_prices(df, priority, AH_COLUMNS[1:3], AH_COLUMNS[3])
    line = pd.to_numeric(df[line_col], errors="coerce") if line_col in df.columns else pd.Series(np.nan, index=df.index)
    ok = line.notna() & out["odds_ah_home"].notna()
    out.insert(0, "ah_line", line.where(ok))
    out.loc[~ok, ["odds_ah_home", "odds_ah_away"]] = np.nan
    out.loc[~ok, "ah_source"] = None
    return out


def select_ou_odds(df: pd.DataFrame, priority: Sequence[Sequence[str]]) -> pd.DataFrame:
    """Over/under 2.5 goals odds: columns odds_over_2_5, odds_under_2_5, ou_source."""
    return select_prices(df, priority, OU_COLUMNS[:2], OU_COLUMNS[2])


def _first_present(df: pd.DataFrame, names: Iterable[str]) -> pd.Series:
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series(np.nan, index=df.index)


def clean_file(raw: pd.DataFrame, league: str, season: str, priority, ou_priority=(), ah_priority=()) -> pd.DataFrame:
    """Turn one raw football-data frame into schema rows (played matches only)."""
    if raw.empty:
        return pd.DataFrame(columns=MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS + HT_COLUMNS)
    home = _first_present(raw, ["HomeTeam", "HT"])
    away = _first_present(raw, ["AwayTeam", "AT"])
    hs = pd.to_numeric(_first_present(raw, ["FTHG", "HG"]), errors="coerce")
    as_ = pd.to_numeric(_first_present(raw, ["FTAG", "AG"]), errors="coerce")
    df = pd.DataFrame(
        {
            "sport": "football",
            "league": league,
            "season": season_label(season),
            "date": parse_dates(_first_present(raw, ["Date"])),
            "home": home,
            "away": away,
            "home_score": hs,
            "away_score": as_,
            "ht_home_score": pd.to_numeric(_first_present(raw, ["HTHG"]), errors="coerce"),
            "ht_away_score": pd.to_numeric(_first_present(raw, ["HTAG"]), errors="coerce"),
        }
    )
    df = pd.concat([df, select_odds(raw, priority), select_ou_odds(raw, ou_priority),
                    select_ah_odds(raw, ah_priority)], axis=1)
    blank = (df["home"].fillna("") == "") | (df["away"].fillna("") == "")
    unparsed = df["date"].isna() & ~blank
    unplayed = (df["home_score"].isna() | df["away_score"].isna()) & ~blank
    if unparsed.any():
        log.warning("%s %s: %d rows with unparseable dates dropped", league, season, unparsed.sum())
    df = df[~blank & ~unparsed & ~unplayed].copy()
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["outcome"] = outcome_from_scores(df["home_score"], df["away_score"])
    if "FTR" in raw.columns:
        ftr = raw.loc[df.index, "FTR"]
        mismatch = (ftr != "") & (ftr != df["outcome"])
        if mismatch.any():
            log.warning("%s %s: %d rows where FTR disagrees with score", league, season, mismatch.sum())
    return df[MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS + HT_COLUMNS]


def load_matches(raw_dir: Path | None = None, leagues: Iterable[str] | None = None) -> pd.DataFrame:
    """Merge all {league}_{season}.csv files into one de-duplicated table."""
    cfg = load_config()["football_data"]
    raw_dir = Path(raw_dir or project_path(load_config()["paths"]["raw_football"]))
    wanted = set(leagues or cfg["leagues"])
    frames = []
    for path in sorted(raw_dir.glob("*.csv")):
        m = FILE_RE.match(path.name)
        if not m or m["league"] not in wanted:
            continue
        frames.append(clean_file(read_raw_csv(path), m["league"], m["season"], cfg["odds_priority"],
                                 cfg.get("ou_odds_priority", []), cfg.get("ah_odds_priority", [])))
    if cfg.get("extra_leagues"):
        from predictor.config import season_label
        from predictor.loaders.football_data_extra import load_extra_leagues

        frames += load_extra_leagues(raw_dir, cfg["extra_leagues"], cfg["extra_odds_priority"],
                                     season_label(cfg["first_season"]), wanted)
    if not frames:
        return pd.DataFrame(columns=MATCH_COLUMNS + ["odds_source"] + OU_COLUMNS + AH_COLUMNS + HT_COLUMNS)
    df = pd.concat(frames, ignore_index=True)
    df = apply_renames(df, cfg.get("team_renames", {}))
    df = drop_excluded(df, cfg.get("excluded_matches", []))
    before = len(df)
    df = df.drop_duplicates(["league", "date", "home", "away"], keep="last")
    if len(df) < before:
        log.info("dropped %d duplicate rows", before - len(df))
    df = df.sort_values(["date", "league", "home"]).reset_index(drop=True)
    validate_matches(df)
    return df


def apply_renames(df: pd.DataFrame, renames: dict) -> pd.DataFrame:
    """Map a club's older names to its current one, per league."""
    for league, mapping in (renames or {}).items():
        m = df["league"] == league
        for col in ("home", "away"):
            df.loc[m, col] = df.loc[m, col].replace(mapping)
    return df


def drop_excluded(df: pd.DataFrame, rules) -> pd.DataFrame:
    """Drop awarded/forfeited results listed in config (they aren't real matches)."""
    drop = pd.Series(False, index=df.index)
    for r in rules:
        drop |= ((df["league"] == r["league"]) & (df["season"] == r["season"])
                 & (df["date"] >= pd.Timestamp(r["from"]))
                 & (df["home"].isin(r["teams"]) | df["away"].isin(r["teams"])))
    if drop.any():
        log.info("excluded %d awarded/forfeited matches", drop.sum())
    return df[~drop]


def season_window_violations(df: pd.DataFrame) -> pd.Series:
    """Rows whose date falls outside the Jul(start)-Aug(end) window of their season.

    Seasons run Aug-Jul; a month of slack each side allows for early starts
    and the 2019-20 COVID extension.
    """
    start_year = df["season"].str[:4].astype(int)
    lo = pd.to_datetime(start_year.astype(str) + "-07-01")
    hi = pd.to_datetime((start_year + 1).astype(str) + "-08-31")
    return (df["date"] < lo) | (df["date"] > hi)
