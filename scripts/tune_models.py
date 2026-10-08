#!/usr/bin/env python
"""Tune model hyperparameters by walk-forward log loss on the TUNE seasons only.

Uses coordinate descent over the grids below. The test seasons in config.yaml
are never touched here. Prints the best settings; copy them into config.yaml.

    python scripts/tune_models.py --model elo
    python scripts/tune_models.py --model dixon_coles
"""
from __future__ import annotations

import argparse
import itertools
import logging
import time

import pandas as pd

from predictor.backtest import walk_forward
from predictor.config import load_config, project_path
from predictor.metrics import score
from predictor.models import get_model

GRIDS = {
    "elo": {
        "k": [10, 15, 20, 25, 30, 40],
        "home_advantage": [30, 45, 60, 75, 90],
        "new_team_offset": [0, -50, -100, -150, -200],
        "season_regression": [0.0, 0.1, 0.2, 0.33, 0.5],
        "relegated_offset": [0, 50, 100, 150, 200, 250],
    },
    "dixon_coles": {
        "half_life_days": [60, 90, 120, 180, 240, 365, 540],
        "l2_penalty": [0.1, 0.3, 1.0, 3.0, 10.0],
        "new_team_quantile": [0.1, 0.2, 0.3, 0.5],
    },
}


def evaluate(name: str, params: dict, matches: pd.DataFrame, mask: pd.Series, freq: str) -> float:
    pred = walk_forward(get_model(name, **params), matches, mask, freq)
    return score(pred)["log_loss"]


def main() -> None:
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(GRIDS), required=True)
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--only", nargs="*", help="tune just these parameters, keep the rest as configured")
    args = ap.parse_args()

    cfg = load_config()
    ev = cfg["evaluation"]
    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    overlap = set(ev["tune_seasons"]) & set(ev["test_seasons"])
    assert not overlap, f"tune/test overlap: {overlap}"
    # the fitted data must never reach into the test period
    first_test = matches.loc[matches["season"].isin(ev["test_seasons"]), "date"].min()
    matches = matches[matches["date"] < first_test].reset_index(drop=True)
    tune_mask = matches["season"].isin(ev["tune_seasons"])

    grid = GRIDS[args.model]
    if args.only:
        grid = {k: v for k, v in grid.items() if k in args.only}
    best = {k: cfg["models"][args.model][k] for k in grid}
    cache: dict[tuple, float] = {}

    def ll(params):
        key = tuple(sorted(params.items()))
        if key not in cache:
            t = time.time()
            cache[key] = evaluate(args.model, params, matches, tune_mask, ev["refit_frequency"])
            print(f"  {params}  log_loss={cache[key]:.5f}  ({time.time() - t:.1f}s)", flush=True)
        return cache[key]

    print(f"Tuning {args.model} on {ev['tune_seasons']} ({tune_mask.sum()} matches)")
    print(f"start: {best} -> {ll(best):.5f}")
    for p in range(args.passes):
        for param, values in grid.items():
            scores = {v: ll({**best, param: v}) for v in values}
            best[param] = min(scores, key=scores.get)
        print(f"after pass {p + 1}: {best} -> {ll(best):.5f}")

    rows = [{**dict(k), "log_loss": v} for k, v in cache.items()]
    out = project_path(cfg["paths"]["processed"]) / f"tuning_{args.model}.csv"
    pd.DataFrame(rows).sort_values("log_loss").to_csv(out, index=False)
    print(f"\nBEST {args.model}: {best}  log_loss={ll(best):.5f}\nall results -> {out}")


if __name__ == "__main__":
    main()
