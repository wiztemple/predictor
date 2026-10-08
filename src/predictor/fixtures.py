"""Upcoming fixtures from football-data.co.uk, fixturedownload.com or a local CSV.

Every source returns: league, kickoff (UTC, tz-aware), home, away, source,
where home/away are the source's own spelling (mapped later).
"""
from __future__ import annotations

import io
import json
import logging
import time
from pathlib import Path

import pandas as pd
import requests

from predictor.loaders.football_data import parse_dates

log = logging.getLogger(__name__)

FIXTURE_COLUMNS = ["league", "kickoff", "home", "away", "source"]


def _get(url: str, user_agent: str, timeout: float = 30) -> requests.Response:
    r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
    r.raise_for_status()
    return r


def parse_football_data_fixtures(content: bytes, leagues, tz: str) -> pd.DataFrame:
    if not content.strip():
        return pd.DataFrame(columns=FIXTURE_COLUMNS)
    df = pd.read_csv(io.BytesIO(content), encoding="latin-1", dtype=str)
    df.columns = [c.replace("ï»¿", "").replace("﻿", "").strip() for c in df.columns]
    df = df[df["Div"].isin(leagues)]
    date = parse_dates(df["Date"])
    time = pd.to_timedelta(df.get("Time", pd.Series("00:00", index=df.index)).fillna("00:00") + ":00")
    kickoff = (date + time).dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    return pd.DataFrame({
        "league": df["Div"], "kickoff": kickoff, "home": df["HomeTeam"].str.strip(),
        "away": df["AwayTeam"].str.strip(), "source": "football-data",
    }).dropna(subset=["kickoff"])


def fetch_football_data(url: str, leagues, tz: str, user_agent: str) -> pd.DataFrame:
    return parse_football_data_fixtures(_get(url, user_agent).content, leagues, tz)


def parse_extra_fixtures(content: bytes, extra: dict, tz: str) -> pd.DataFrame:
    """football-data new_league_fixtures.csv (Country, League, Date, Time, Home, Away; UK time)
    -> fixtures for the configured extra leagues."""
    if not content.strip():
        return pd.DataFrame(columns=FIXTURE_COLUMNS)
    df = pd.read_csv(io.BytesIO(content), encoding="latin-1", dtype=str)
    df.columns = [c.replace("ï»¿", "").replace("\ufeff", "").strip() for c in df.columns]
    lookup = {(m["country"], m["league"]): code for code, m in extra.items()}
    code = [lookup.get((c.strip(), l.strip())) for c, l in zip(df["Country"].fillna(""), df["League"].fillna(""))]
    df = df.assign(code=code).dropna(subset=["code"])
    if df.empty:
        return pd.DataFrame(columns=FIXTURE_COLUMNS)
    date = parse_dates(df["Date"])
    time_ = pd.to_timedelta(df["Time"].fillna("00:00") + ":00")
    kickoff = (date + time_).dt.tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward").dt.tz_convert("UTC")
    return pd.DataFrame({
        "league": df["code"], "kickoff": kickoff, "home": df["Home"].str.strip(), "away": df["Away"].str.strip(),
        "source": "football-data-extra",
    }).dropna(subset=["kickoff"])


def fetch_extra_fixtures(url: str, extra: dict, tz: str, user_agent: str) -> pd.DataFrame:
    return parse_extra_fixtures(_get(url, user_agent).content, extra, tz)


def parse_fixturedownload(records: list[dict], league: str) -> pd.DataFrame:
    df = pd.DataFrame(records)
    if df.empty:
        return pd.DataFrame(columns=FIXTURE_COLUMNS)
    df = df[df["HomeTeamScore"].isna()]  # unplayed only
    return pd.DataFrame({
        "league": league, "kickoff": pd.to_datetime(df["DateUtc"], utc=True),
        "home": df["HomeTeam"].str.strip(), "away": df["AwayTeam"].str.strip(), "source": "fixturedownload",
    })


def _get_json_with_retries(url: str, user_agent: str, retries: int, backoff: float):
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return _get(url, user_agent).json()
        except Exception as e:  # timeouts, resets, 5xx, bad JSON
            last = e
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
    raise RuntimeError(str(last))


def fetch_fixturedownload(url_tmpl: str, slugs: dict[str, str], season_year: int, user_agent: str,
                          cache_dir: Path | None = None, retries: int = 3, backoff: float = 5.0) -> pd.DataFrame:
    """Fetch each league's schedule. On failure after retries, fall back to the last
    successfully fetched copy in `cache_dir` (schedules change rarely) and warn."""
    frames = []
    for league, slug in slugs.items():
        url = url_tmpl.format(slug=slug, year=season_year)
        cache = Path(cache_dir) / f"{slug}-{season_year}.json" if cache_dir else None
        try:
            records = _get_json_with_retries(url, user_agent, retries, backoff)
            if cache is not None:
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_text(json.dumps(records))
        except Exception as e:
            if cache is not None and cache.exists():
                age_h = (time.time() - cache.stat().st_mtime) / 3600
                log.warning("fixturedownload %s failed (%s); USING CACHED COPY from %.0f hours ago", url, e, age_h)
                records = json.loads(cache.read_text())
            else:
                log.error("fixturedownload %s failed and no cached copy: %s fixtures missing", url, league)
                continue
        frames.append(parse_fixturedownload(records, league))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=FIXTURE_COLUMNS)


def load_fixture_csv(path: Path) -> pd.DataFrame:
    """User CSV with columns league, home, away and kickoff (ISO, UTC) or date (+ optional time)."""
    df = pd.read_csv(path, dtype=str)
    if "kickoff" in df.columns:
        kickoff = pd.to_datetime(df["kickoff"], utc=True)
    else:
        kickoff = pd.to_datetime(df["date"] + " " + df.get("time", pd.Series("00:00", index=df.index)).fillna("00:00"),
                                 dayfirst=True, utc=True)
    return pd.DataFrame({"league": df["league"], "kickoff": kickoff, "home": df["home"].str.strip(),
                         "away": df["away"].str.strip(), "source": f"csv:{Path(path).name}"})


def combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate sources; earlier frames win on duplicates.

    Duplicates are the same league + mapped home + mapped away. Within a short
    horizon a pairing occurs once, and ignoring the date means a match that one
    source has rescheduled is not listed twice. Expects home_mapped/away_mapped.
    """
    frames = [f for f in frames if len(f)]
    if not frames:
        return pd.DataFrame(columns=FIXTURE_COLUMNS + ["home_mapped", "away_mapped"])
    df = pd.concat(frames, ignore_index=True)
    key_home = df["home_mapped"].fillna("?" + df["home"])
    key_away = df["away_mapped"].fillna("?" + df["away"])
    dup = pd.DataFrame({"l": df["league"], "h": key_home, "a": key_away}).duplicated()
    return df[~dup].sort_values(["kickoff", "league", "home"]).reset_index(drop=True)
