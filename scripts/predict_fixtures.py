#!/usr/bin/env python
"""Predict upcoming fixtures and write predictions.json.

Fixture sources, in priority order (earlier wins on duplicates):
  1. --fixtures CSV you provide (columns: league, home, away, kickoff | date[, time])
  2. football-data.co.uk fixtures.csv
  3. fixturedownload.com season schedules

Teams that can't be mapped to the historical names are reported (stdout and
the "unmatched" list in the JSON) - never silently dropped.

    python scripts/predict_fixtures.py
    python scripts/predict_fixtures.py --fixtures my_fixtures.csv --no-online
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

import pandas as pd

from predictor.config import load_config, project_path, season_of
from predictor.export import build_document
from predictor.fixtures import (
    combine,
    fetch_extra_fixtures,
    fetch_fixturedownload,
    fetch_football_data,
    load_fixture_csv,
)
from predictor.models import get_model
from predictor.teams import TeamNameMapper
from predictor.store import connect, database_url, lock_weekly, log_picks
from predictor.tracking import log_predictions

log = logging.getLogger("predict_fixtures")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = load_config()
    fd, fx_cfg, pr_cfg = cfg["football_data"], cfg["fixtures"], cfg["predictions"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures", help="local fixtures CSV")
    ap.add_argument("--no-online", action="store_true", help="skip online fixture sources")
    ap.add_argument("--horizon-days", type=int, default=fx_cfg["horizon_days"])
    ap.add_argument("--output", default=pr_cfg["output"])
    ap.add_argument("--no-log", action="store_true", help="don't append to the prediction log")
    args = ap.parse_args()

    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    leagues = list(fd["leagues"])
    mapper = TeamNameMapper.from_history(matches, project_path(fx_cfg["team_names"]))
    bad = mapper.unknown_aliases()
    if bad:
        log.warning("team_names.yaml targets not found in history (check spelling): %s", bad)

    now = pd.Timestamp.now(tz="UTC")
    sources = []
    if args.fixtures:
        sources.append(load_fixture_csv(args.fixtures))
    if not args.no_online:
        try:
            sources.append(fetch_football_data(fd["fixtures_url"], leagues, fx_cfg["football_data_timezone"], fd["user_agent"]))
        except Exception as e:
            log.warning("football-data fixtures.csv failed: %s", e)
        if fd.get("extra_leagues"):
            try:
                sources.append(fetch_extra_fixtures(fd["extra_fixtures_url"], fd["extra_leagues"],
                                                    fx_cfg["football_data_timezone"], fd["user_agent"]))
            except Exception as e:
                log.warning("football-data new_league_fixtures.csv failed: %s", e)
        year = int(season_of(now.tz_convert(None))[:4])
        sources.append(fetch_fixturedownload(fx_cfg["fixturedownload_url"], fx_cfg["fixturedownload_slugs"], year,
                                             fd["user_agent"], cache_dir=project_path(fx_cfg["cache_dir"])))
    for s in sources:
        log.info("source %-16s %4d fixtures", s["source"].iat[0] if len(s) else "(empty)", len(s))

    # keep the window, then map names per source
    horizon = now + pd.Timedelta(days=args.horizon_days)
    fitted_until = matches["date"].max()
    mapped = []
    for s in sources:
        s = s[s["league"].isin(leagues) & (s["kickoff"] >= now) & (s["kickoff"] <= horizon)].copy()
        s["home_mapped"] = [mapper.match(l, n) for l, n in zip(s["league"], s["home"])]
        s["away_mapped"] = [mapper.match(l, n) for l, n in zip(s["league"], s["away"])]
        mapped.append(s)
    fixtures = combine(mapped)
    if fixtures.empty:  # off-season / long break: publish an empty list rather than fail the job
        log.warning("no fixtures in the next %d days from any source", args.horizon_days)

    ok = fixtures["home_mapped"].notna() & fixtures["away_mapped"].notna()
    unmatched = []
    for _, f in fixtures[~ok].iterrows():
        for side in ("home", "away"):
            if pd.isna(f[f"{side}_mapped"]):
                unmatched.append({
                    "league": f["league"], "kickoff": f["kickoff"].isoformat().replace("+00:00", "Z"),
                    "fixture": f"{f['home']} vs {f['away']}", "unmatched_name": f[side],
                    "source": f["source"], "suggestions": mapper.suggest(f["league"], f[side]),
                })
    good = fixtures[ok].copy()
    good["season"] = [season_of(k.tz_convert(None)) for k in good["kickoff"]]
    too_early = (good["kickoff"].dt.tz_convert(None).dt.normalize() <= fitted_until) if len(good) else pd.Series(False, index=good.index)
    if too_early.any():
        log.warning("%d fixtures dated on/before last result (%s) skipped", too_early.sum(), f"{fitted_until:%Y-%m-%d}")
        good = good[~too_early]

    primary = get_model(pr_cfg["primary_model"]).fit(matches)
    secondary = [get_model(n).fit(matches) for n in pr_cfg["secondary_models"]]
    cal_path = project_path(pr_cfg["goals_calibration"])
    goals_cal = json.loads(cal_path.read_text()) if cal_path.exists() else None
    if goals_cal is None:
        log.warning("no goals calibration at %s (run scripts/backtest.py); goals markets uncalibrated", cal_path)
    doc = build_document(good, primary, secondary, unmatched, fd["leagues"], fitted_until,
                         pr_cfg["status"], pr_cfg["grid_max_goals"], goals_calibration=goals_cal,
                         pick_markets=cfg["picks"]["markets"], ten_min_share=cfg["timing"]["share_10"],
                         half_share=cfg["timing"]["share_45"])

    out = project_path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
    if not args.no_log:
        added, same = log_predictions(doc, project_path(cfg["tracking"]["log_dir"]), now.to_pydatetime())
        log.info("prediction log: %d new entries, %d unchanged", added, same)
        engine = connect(database_url(cfg["picks"], project_path(".")))
        added, same = log_picks(engine, doc, cfg["picks"]["markets"], now.to_pydatetime())
        log.info("picks database (%s): %d new picks, %d unchanged", engine.url.get_backend_name(), added, same)
        locked = lock_weekly(engine, doc, cfg["picks"]["markets"], now.to_pydatetime(), cfg["picks"]["per_week"])
        if locked:
            log.info("weekly top %d locked for this week (%d picks)", cfg["picks"]["per_week"], locked)

    print(f"\n{len(doc['predictions'])} predictions -> {args.output}  (data through {doc['data_through']}, status={doc['status']})")
    if len(good):
        print(good.groupby("league").size().rename("fixtures").to_string())
    missing = [lg for lg in leagues if lg not in set(good["league"])]
    if missing:
        print(f"\nNOTE: no fixtures in the next {args.horizon_days} days for {missing} (break, or feed failure above)")
    if unmatched:
        print(f"\nUNMATCHED TEAM NAMES ({len(unmatched)}) - add to {fx_cfg['team_names']}:")
        for u in unmatched:
            print(f"  {u['league']:4} {u['unmatched_name']!r:30} in {u['fixture']}  [{u['source']}]  suggestions: {u['suggestions']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
