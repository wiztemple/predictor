"""Backup results from ESPN's public scoreboard feed, for when football-data.co.uk is behind.

football-data stays the source of record: ESPN rows are only used for dates after
a league's last football-data result, so they drop out by themselves once
football-data catches up (and brings closing odds and half-time scores, which
ESPN rows lack). Team names map through team_names.yaml only - an unknown name
is reported and the match left out, never guessed.

Each league-day is cached as raw JSON under `cache_dir/{slug}/{YYYYMMDD}.json`;
days older than `refresh_days` are not fetched again.
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from predictor.config import season_of
from predictor.schema import outcome_from_scores

log = logging.getLogger(__name__)

FINISHED = {"STATUS_FULL_TIME", "STATUS_FINAL"}
RAW_COLUMNS = ["league", "kickoff", "home", "away", "home_score", "away_score", "home_corners", "away_corners"]


def parse_results(payload: dict, league: str) -> pd.DataFrame:
    """Finished matches only (postponed/abandoned/in-play are skipped)."""
    rows = []
    for ev in payload.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        st = (comp.get("status") or ev.get("status") or {}).get("type", {})
        if not st.get("completed") or st.get("name") not in FINISHED:
            continue
        sides = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        h, a = sides.get("home"), sides.get("away")
        if not h or not a or not ev.get("date"):
            continue
        try:
            hs, as_ = int(h["score"]), int(a["score"])
        except (KeyError, TypeError, ValueError):
            continue

        def corners(c):
            v = {s.get("name"): s.get("displayValue") for s in c.get("statistics", [])}.get("wonCorners")
            try:
                return float(v)
            except (TypeError, ValueError):
                return np.nan

        k = pd.Timestamp(ev["date"])
        k = k.tz_convert("UTC") if k.tzinfo else k.tz_localize("UTC")
        rows.append((league, k, h["team"]["displayName"].strip(), a["team"]["displayName"].strip(),
                     hs, as_, corners(h), corners(a)))
    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def fetch_espn_results(url_tmpl: str, slugs: dict[str, str], since: dict[str, pd.Timestamp], until: pd.Timestamp,
                       cache_dir: Path, get_json, delay: float = 0.3, refresh_days: int = 2,
                       max_days: int = 60) -> tuple[int, list[str]]:
    """Fetch every day after `since[league]` up to `until` (dates, UK). Returns (fetched, failed)."""
    fetched, failed = 0, []
    fresh_from = until - pd.Timedelta(days=refresh_days)
    for league, slug in slugs.items():
        start = since.get(league)
        if start is None:
            continue
        start = max(start + pd.Timedelta(days=1), until - pd.Timedelta(days=max_days))
        for day in pd.date_range(start, until, freq="D"):
            dest = Path(cache_dir) / slug / f"{day:%Y%m%d}.json"
            if dest.exists() and day < fresh_from:
                continue
            try:
                payload = get_json(url_tmpl.format(slug=slug, date=f"{day:%Y%m%d}"))
            except Exception as e:  # keep going; a missing day just stays missing until next run
                failed.append(f"{slug} {day:%Y-%m-%d}: {e}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(payload))
            fetched += 1
            time.sleep(delay)
    return fetched, failed


def load_espn_results(cache_dir: Path, slugs: dict[str, str], mapper, after: dict[str, pd.Timestamp],
                      columns: list[str]) -> tuple[pd.DataFrame, list[dict]]:
    """Cached ESPN results as schema rows dated after `after[league]`, plus unmatched names."""
    frames = []
    for league, slug in slugs.items():
        cut = after.get(league)
        if cut is None:
            continue
        for f in sorted((Path(cache_dir) / slug).glob("*.json")):
            if pd.Timestamp(f.stem) <= cut - pd.Timedelta(days=1):  # kickoff dates can shift a day across UTC
                continue
            day = parse_results(json.loads(f.read_text()), league)
            if len(day):
                frames.append(day)
    if not frames:
        return pd.DataFrame(columns=columns), []
    raw = pd.concat(frames, ignore_index=True).drop_duplicates(["league", "kickoff", "home", "away"])
    raw["date"] = raw["kickoff"].dt.tz_convert("Europe/London").dt.tz_localize(None).dt.normalize()
    raw = raw[raw["date"] > raw["league"].map(after)]

    unmatched = []
    for side in ("home", "away"):
        mapped = [mapper.match(lg, n) for lg, n in zip(raw["league"], raw[side])]
        for lg, n, m in zip(raw["league"], raw[side], mapped):
            if m is None:
                unmatched.append({"league": lg, "name": n, "suggestions": mapper.suggest(lg, n)})
        raw[side] = mapped
    raw = raw.dropna(subset=["home", "away"])

    df = pd.DataFrame({
        "sport": "football", "league": raw["league"], "season": [season_of(d, league=lg) for d, lg in zip(raw["date"], raw["league"])],
        "date": raw["date"], "home": raw["home"], "away": raw["away"],
        "home_score": raw["home_score"].astype(int), "away_score": raw["away_score"].astype(int),
        "home_corners": raw["home_corners"], "away_corners": raw["away_corners"],
    })
    df["outcome"] = outcome_from_scores(df["home_score"], df["away_score"])
    for c in columns:
        if c not in df.columns:
            df[c] = None if c.endswith("source") else np.nan
    df["results_source"] = "espn"
    uniq = {(u["league"], u["name"]): u for u in unmatched}
    return df[columns].reset_index(drop=True), list(uniq.values())
