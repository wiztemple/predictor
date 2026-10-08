#!/usr/bin/env python
"""Score logged pre-kickoff predictions against results -> live_summary.json.

The official prediction for a match is the latest one logged before kickoff.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from predictor.config import load_config, project_path
from predictor.tracking import attach_results, live_summary, load_log, official_predictions


def main() -> int:
    cfg = load_config()
    tr = cfg["tracking"]
    now = pd.Timestamp.now(tz="UTC")
    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    entries = load_log(project_path(tr["log_dir"]))
    scored = attach_results(official_predictions(entries), matches, now,
                            tr["date_tolerance_days"], tr["void_after_days"])
    summary = live_summary(scored, cfg["predictions"]["primary_model"])
    summary["generated_at"] = now.isoformat(timespec="seconds")
    summary["log_entries"] = len(entries)
    out = project_path(tr["live_summary"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    print(f"log entries {len(entries)}; matches {summary['n_logged_matches']}: "
          f"{summary['n_scored']} scored, {summary['n_pending']} pending, {summary['n_void']} void")
    if summary.get("same_matches_with_odds"):
        s = summary["same_matches_with_odds"]
        print(f"log loss on {s['n']} matches: model {s['model']['log_loss']:.4f} vs bookmaker {s['bookmaker']['log_loss']:.4f}")
    print(f"-> {tr['live_summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
