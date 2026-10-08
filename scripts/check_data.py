#!/usr/bin/env python
"""Print match and odds coverage per league and season; warn about gaps.

Reads data/processed/matches.parquet (run build_dataset.py first).
"""
from __future__ import annotations

import sys

import pandas as pd

from predictor.config import load_config, project_path, season_codes, season_label
from predictor.loaders.football_data import season_window_violations


def main() -> int:
    cfg = load_config()
    fd = cfg["football_data"]
    path = project_path(cfg["paths"]["matches"])
    if not path.exists():
        print(f"ERROR: {path} not found; run scripts/build_dataset.py")
        return 1
    df = pd.read_parquet(path)
    warnings: list[str] = []

    seasons = [season_label(s) for s in season_codes(fd["first_season"], fd["last_season"])]
    current = seasons[-1]

    print(f"{len(df):,} matches, {df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d}\n")
    header = f"{'league':6} {'season':8} {'matches':>7} {'teams':>5} {'expect':>6} {'odds%':>6} {'closing%':>8}  {'first':10} {'last':10}"
    print(header)
    print("-" * len(header))

    for league in fd["leagues"]:
        ldf = df[df["league"] == league]
        if ldf.empty:
            warnings.append(f"league {league} ({fd['leagues'][league]}) has no data at all")
            continue
        for season in seasons:
            s = ldf[ldf["season"] == season]
            if s.empty:
                warnings.append(f"{league} {season}: no matches")
                continue
            teams = pd.unique(s[["home", "away"]].values.ravel())
            expected = len(teams) * (len(teams) - 1)
            odds = s["odds_home"].notna().mean() * 100
            closing = s["odds_source"].fillna("").str.endswith("closing").mean() * 100
            print(
                f"{league:6} {season:8} {len(s):7d} {len(teams):5d} {expected:6d} {odds:6.1f} {closing:8.1f}  "
                f"{s['date'].min():%Y-%m-%d} {s['date'].max():%Y-%m-%d}"
            )
            # Some leagues add rounds (Scotland's split) or playoffs (Belgium, Greece), so only
            # fewer matches than a double round-robin is suspicious.
            if season != current and len(s) < expected:
                warnings.append(f"{league} {season}: {len(s)} matches but {len(teams)} teams imply at least {expected}")
            if odds < 99:
                warnings.append(f"{league} {season}: odds missing for {100 - odds:.1f}% of matches")
        print()

    print("Odds source breakdown (share of all matches):")
    print(df["odds_source"].fillna("none").value_counts(normalize=True).mul(100).round(2).to_string())
    print()

    out_of_window = season_window_violations(df)
    if out_of_window.any():
        warnings.append(f"{out_of_window.sum()} matches dated outside their season's Aug-Jul window")

    cur = df[df["season"] == current]
    print(f"Current season {current}: {len(cur)} matches played so far, latest {cur['date'].max():%Y-%m-%d}"
          if len(cur) else f"Current season {current}: no matches yet")

    print(f"\n{len(warnings)} warning(s)")
    for w in warnings:
        print(f"  WARN {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
