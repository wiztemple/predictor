#!/usr/bin/env python
"""Merge raw football CSVs into data/processed/matches.parquet."""
from __future__ import annotations

import logging

from predictor.config import load_config, project_path
from predictor.loaders.football_data import load_matches


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    df = load_matches()
    out = project_path(load_config()["paths"]["matches"])
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Wrote {len(df):,} matches to {out.relative_to(project_path('.'))}")


if __name__ == "__main__":
    main()
