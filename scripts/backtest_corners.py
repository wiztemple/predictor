#!/usr/bin/env python
"""Walk-forward backtest of the total-corners model.

    python scripts/backtest_corners.py --tune   # grid on the tune seasons only -> pick settings for config.yaml
    python scripts/backtest_corners.py          # test seasons with the settings in config.yaml

No bookmaker corner odds are in our data, so the benchmark is a league-average
baseline (each league's mean total over the past year). Refits weekly (Tue-Mon),
on matches strictly before each week.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from predictor.config import load_config, project_path
from predictor.corners import (CornersModel, LeagueAverageCorners, count_log_lik, fit_dispersion, line_key)
from predictor.metrics import binary_reliability, binary_scores, cluster_bootstrap_mean

GRID_HALF_LIFE = [180, 365, 730]
GRID_L2 = [30.0, 60.0, 100.0, 200.0, 400.0]
THRESHOLDS = [0.55, 0.6, 0.65, 0.7, 0.75, 0.8]


def walk(model, matches: pd.DataFrame, mask: pd.Series, freq: str) -> pd.DataFrame:
    test = matches[mask]
    out = []
    for period, fx in test.groupby(test["date"].dt.to_period(freq), sort=True):
        model.fit(matches, as_of=period.start_time)
        p = model.predict(fx)
        p["total"] = (fx["home_corners"] + fx["away_corners"]).to_numpy()
        p["season"] = fx["season"].to_numpy()
        p["cutoff"] = period.start_time
        out.append(p)
    return pd.concat(out, ignore_index=True).dropna(subset=["exp_corners", "total"])


def tune(matches, cfg, freq) -> None:
    mask = matches["season"].isin(cfg["evaluation"]["tune_seasons"])
    c = cfg["models"]["corners"]
    rows = []
    for hl, l2 in itertools.product(GRID_HALF_LIFE, GRID_L2):
        p = walk(CornersModel(hl, l2, c["max_history_days"], None, c["new_team_quantile"]), matches, mask, freq)
        k = fit_dispersion(p["exp_corners"], p["total"])
        ll = -count_log_lik(p["exp_corners"], p["total"], k).mean()
        rows.append({"half_life_days": hl, "l2_penalty": l2, "dispersion_k": round(k, 1), "log_loss": ll, "n": len(p)})
        print(f"half-life {hl:4d}  l2 {l2:5.1f}  k {k:7.1f}  count log loss {ll:.5f}", flush=True)
    t = pd.DataFrame(rows).sort_values("log_loss")
    base = walk(LeagueAverageCorners(c["baseline_days"]), matches, mask, freq)
    bk = fit_dispersion(base["exp_corners"], base["total"])
    print(f"\nbaseline (league average, {c['baseline_days']} days): k {bk:.1f}  "
          f"log loss {-count_log_lik(base['exp_corners'], base['total'], bk).mean():.5f}")
    best = t.iloc[0]
    print(f"\nBEST on tune seasons: half_life_days {best.half_life_days}, l2_penalty {best.l2_penalty}, "
          f"dispersion_k {best.dispersion_k}; baseline_dispersion_k {bk:.1f}")
    out = project_path("data/backtest/corners_tuning.csv")
    t.to_csv(out, index=False)
    print(f"-> {out}")


def evaluate(matches, cfg, freq) -> dict:
    c = cfg["models"]["corners"]
    mask = matches["season"].isin(cfg["evaluation"]["test_seasons"])
    model = walk(CornersModel.from_config(cfg), matches, mask, freq)
    base = walk(LeagueAverageCorners(c["baseline_days"], c["baseline_dispersion_k"]), matches, mask, freq)
    key = ["league", "date", "home", "away"]
    t = model.merge(base[key + ["exp_corners"] + [f"p_{line_key(l)}" for l in c["lines"]]],
                    on=key, suffixes=("", "_base"))
    y_total = t["total"].to_numpy()
    ll_m = -count_log_lik(t["exp_corners"], y_total, c["dispersion_k"])
    ll_b = -count_log_lik(t["exp_corners_base"], y_total, c["baseline_dispersion_k"])
    gain, lo, hi = cluster_bootstrap_mean(ll_b - ll_m, t["cutoff"])
    res = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "test_seasons": cfg["evaluation"]["test_seasons"],
        "n_matches": int(len(t)),
        "settings": {k: c[k] for k in ("half_life_days", "l2_penalty", "dispersion_k", "baseline_days",
                                       "baseline_dispersion_k")},
        "benchmark": "league average (no bookmaker corner odds in our data)",
        "mean_total": float(y_total.mean()),
        "mean_predicted": float(t["exp_corners"].mean()),
        "count_log_loss": {"model": float(ll_m.mean()), "baseline": float(ll_b.mean()),
                           "gain": gain, "gain_ci": [lo, hi]},
        "lines": {},
    }
    print(f"{len(t):,} test matches; mean total {y_total.mean():.2f}, model mean {t['exp_corners'].mean():.2f}")
    print(f"count log loss: model {ll_m.mean():.4f}  baseline {ll_b.mean():.4f}  "
          f"gain {gain:+.4f} [95% CI {lo:+.4f}, {hi:+.4f}]\n")
    for line in c["lines"]:
        k = line_key(line)
        p, pb = t[f"p_{k}"].to_numpy(), t[f"p_{k}_base"].to_numpy()
        y = (y_total > line).astype(float)
        sm, sb = binary_scores(p, y), binary_scores(pb, y)
        d = -(y * np.log(pb) + (1 - y) * np.log(1 - pb)) + (y * np.log(p) + (1 - y) * np.log(1 - p))
        g, glo, ghi = cluster_bootstrap_mean(d, t["cutoff"])
        thr = []
        for side, ps, ys in (("over", p, y), ("under", 1 - p, 1 - y)):
            for mp in THRESHOLDS:
                m = ps >= mp
                if m.sum():
                    thr.append({"direction": side, "min_p": mp, "n": int(m.sum()),
                                "mean_pred": float(ps[m].mean()), "hit_rate": float(ys[m].mean())})
        res["lines"][k] = {
            "line": line, "base_rate": float(y.mean()), "model": sm, "baseline": sb,
            "log_loss_gain": g, "log_loss_gain_ci": [glo, ghi],
            "reliability": binary_reliability(p, y).to_dict("records"), "thresholds": thr,
        }
        print(f"over {line:4}: rate {y.mean():.3f}  log loss model {sm['log_loss']:.4f} base {sb['log_loss']:.4f} "
              f"gain {g:+.4f} [{glo:+.4f}, {ghi:+.4f}]  brier {sm['brier']:.4f} vs {sb['brier']:.4f}")
        for r in thr:
            if r["n"] >= 30:
                print(f"     {r['direction']:5} p>={r['min_p']:.2f}: n {r['n']:5d}  predicted {r['mean_pred']:.3f}  "
                      f"won {r['hit_rate']:.3f}")
    by_lg = t.groupby("league").agg(n=("total", "size"), actual=("total", "mean"), predicted=("exp_corners", "mean"))
    res["by_league"] = by_lg.round(3).reset_index().to_dict("records")
    print("\nby league (mean total, actual vs predicted):\n" + by_lg.round(2).to_string())
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", action="store_true", help="grid search on the tune seasons only")
    args = ap.parse_args()
    cfg = load_config()
    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    freq = cfg["evaluation"]["refit_frequency"]
    if args.tune:
        tune(matches, cfg, freq)
        return 0
    res = evaluate(matches, cfg, freq)
    out = project_path(cfg["models"]["corners"]["backtest_output"])
    out.write_text(json.dumps(res, indent=1))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
