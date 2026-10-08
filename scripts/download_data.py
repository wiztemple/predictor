#!/usr/bin/env python
"""Download football-data.co.uk CSVs: one file per league per season.

Completed seasons already on disk are skipped; the current (last) season is
always re-downloaded because it is still being played.

    python scripts/download_data.py               # all leagues, all seasons
    python scripts/download_data.py --leagues E0 --force
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import requests

from predictor.config import load_config, project_path, season_codes


def looks_like_csv(content: bytes) -> bool:
    head = content[:200].lstrip(b"\xef\xbb\xbf").lstrip()
    return (head.startswith(b"Div") or head.startswith(b"HomeTeam") or b",HomeTeam," in head
            or head.startswith(b"Country,League,Season"))


def fetch(session: requests.Session, url: str, timeout: float, retries: int, delay: float) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = session.get(url, timeout=timeout)
            if r.status_code == 404:
                raise FileNotFoundError(f"404 Not Found")
            r.raise_for_status()
            if not looks_like_csv(r.content):
                raise ValueError("response is not a football-data CSV")
            return r.content
        except FileNotFoundError:
            raise
        except Exception as e:  # network errors, 5xx, bad content
            last_err = e
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(str(last_err))


def main() -> int:
    cfg = load_config()["football_data"]
    p = argparse.ArgumentParser()
    p.add_argument("--leagues", nargs="*", default=list(cfg["leagues"]))
    p.add_argument("--first-season", default=cfg["first_season"])
    p.add_argument("--last-season", default=cfg["last_season"])
    p.add_argument("--force", action="store_true", help="re-download files already on disk")
    args = p.parse_args()

    out_dir = project_path(load_config()["paths"]["raw_football"])
    out_dir.mkdir(parents=True, exist_ok=True)
    seasons = season_codes(args.first_season, args.last_season)
    current = seasons[-1]

    session = requests.Session()
    session.headers["User-Agent"] = cfg["user_agent"]
    delay = cfg["request_delay_seconds"]

    extra = cfg.get("extra_leagues", {})
    ok, skipped, failures = 0, 0, []
    for league in [lg for lg in args.leagues if lg not in extra]:
        for season in seasons:
            dest = out_dir / f"{league}_{season}.csv"
            if dest.exists() and not args.force and season != current:
                skipped += 1
                continue
            url = cfg["base_url"].format(season=season, league=league)
            try:
                content = fetch(session, url, cfg["request_timeout_seconds"], cfg["retries"], delay)
                dest.write_bytes(content)
                ok += 1
                print(f"  ok   {league}_{season}  ({len(content):,} bytes)")
            except Exception as e:
                failures.append((league, season, url, str(e)))
                print(f"  FAIL {league}_{season}  {e}")
            time.sleep(delay)

    # extra leagues: one file per league holding every season -> always refresh
    (out_dir / "extra").mkdir(exist_ok=True)
    for league in [lg for lg in args.leagues if lg in extra]:
        url = cfg["extra_base_url"].format(code=league)
        try:
            content = fetch(session, url, cfg["request_timeout_seconds"], cfg["retries"], delay)
            (out_dir / "extra" / f"{league}.csv").write_bytes(content)
            ok += 1
            print(f"  ok   {league} (all seasons)  ({len(content):,} bytes)")
        except Exception as e:
            failures.append((league, "all", url, str(e)))
            print(f"  FAIL {league}  {e}")
        time.sleep(delay)

    print(f"\nDownloaded {ok}, skipped {skipped} (already on disk), failed {len(failures)}.")
    for league, season, url, err in failures:
        print(f"  failure: {league} {season}: {err}  [{url}]")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
