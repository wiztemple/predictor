#!/usr/bin/env python
"""Settle finished matches' picks in the database and export the record for the site.

The official pick for a match is the latest one logged before kickoff. Writes
data/picks/summary.json (read by the frontend).
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from predictor.config import load_config, project_path
from predictor.store import (
    connect,
    database_url,
    export_audit,
    settle,
    settle_weekly,
    summary,
    weekly_summary,
)


def main() -> int:
    cfg = load_config()
    pc, tr = cfg["picks"], cfg["tracking"]
    engine = connect(database_url(pc, project_path(".")))
    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    counts = settle(engine, matches, pd.Timestamp.now(tz="UTC").to_pydatetime(),
                    tr["date_tolerance_days"], tr["void_after_days"])
    weekly_counts = settle_weekly(engine, matches, pd.Timestamp.now(tz="UTC").to_pydatetime(),
                                  tr["date_tolerance_days"], tr["void_after_days"])
    project_path(pc["weekly"]).write_text(json.dumps(weekly_summary(engine, pc["weekly_lists"]), indent=1, default=float))
    print(f"weekly top {pc['per_week']}: newly settled {weekly_counts} -> {pc['weekly']}")
    audit = export_audit(engine, project_path(pc["audit_dir"]))
    print(f"audit export: {audit} -> {pc['audit_dir']}")
    s = summary(engine, pc["per_day"])
    out = project_path(pc["summary"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(s, indent=1, default=float))
    t = s["top"]
    print(f"database: {engine.url.get_backend_name()} | newly settled: {counts} | "
          f"top-{pc['per_day']} record: {t.get('won', 0)}/{t.get('n', 0)}"
          + (f" ({t['hit_rate']:.1%} vs predicted {t['avg_probability']:.1%})" if t.get("n") else ""))
    print(f"-> {pc['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
