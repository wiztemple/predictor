#!/usr/bin/env python
"""One-off: copy picks from the local SQLite fallback into the real database.

    DATABASE_URL=postgres://... python scripts/migrate_picks.py

Rows already present in the target (same match_id + logged_at, or same settled
match_id) are skipped, so it is safe to run more than once.
"""
from __future__ import annotations

import os
import sys

from sqlalchemy import select

from predictor.config import load_config, load_env, project_path
from predictor.store import connect, database_url, official_picks, picks_log


def main() -> int:
    pc = load_config()["picks"]
    load_env(project_path(".env"))
    if not os.environ.get(pc.get("database_url_env", "DATABASE_URL")):
        print("Set DATABASE_URL to the target database first.")
        return 1
    src = connect(f"sqlite:///{project_path(pc['sqlite_fallback'])}")
    dst = connect(database_url(pc, project_path(".")))
    with src.connect() as s, dst.begin() as d:
        have = {(r.match_id, r.logged_at) for r in d.execute(select(picks_log.c.match_id, picks_log.c.logged_at))}
        logs = [dict(r) for r in s.execute(select(picks_log).order_by(picks_log.c.id)).mappings()]
        new_logs = [{k: v for k, v in r.items() if k != "id"} for r in logs if (r["match_id"], r["logged_at"]) not in have]
        if new_logs:
            d.execute(picks_log.insert(), new_logs)
        settled = {r[0] for r in d.execute(select(official_picks.c.match_id))}
        offs = [dict(r) for r in s.execute(select(official_picks)).mappings() if r["match_id"] not in settled]
        if offs:
            d.execute(official_picks.insert(), offs)
    print(f"copied {len(new_logs)} logged picks and {len(offs)} settled picks to {dst.url.get_backend_name()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
