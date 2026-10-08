#!/usr/bin/env python
"""Backtest the cross-market picks rule on the walk-forward test predictions.

Uses data/backtest/predictions.parquet (written by scripts/backtest.py): the
production model's 1X2 and calibrated goals probabilities exactly as they would
have been shown before each match. Writes data/picks/backtest.json.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from predictor.config import load_config, project_path
from predictor.picks import best_pick, closing_odds, market_probability, won


def summarise(df: pd.DataFrame) -> dict:
    out = {"n": int(len(df)), "won": int(df["won"].sum()),
           "hit_rate": float(df["won"].mean()) if len(df) else None,
           "avg_probability": float(df["probability"].mean()) if len(df) else None}
    mp = df.dropna(subset=["market_probability"])
    if len(mp):
        out["vs_market"] = {"n": int(len(mp)), "ours": float(mp["probability"].mean()),
                            "market": float(mp["market_probability"].mean()), "hit_rate": float(mp["won"].mean())}
    priced = df.dropna(subset=["odds"])
    if len(priced):
        profit = np.where(priced["won"], priced["odds"] - 1, -1.0)
        out["priced"] = {"n": int(len(priced)), "avg_odds": float(priced["odds"].mean()),
                         "profit_units": float(profit.sum()), "roi": float(profit.mean())}
    return out


def main() -> None:
    cfg = load_config()
    pc = cfg["picks"]
    bt = pd.read_parquet(project_path("data/backtest/predictions.parquet"))
    prod = json.loads(project_path("data/backtest/summary.json").read_text())["production_model"]

    df = bt.copy()
    picks = []
    for i, r in df.iterrows():
        probs = {"home": r[f"{prod}:p_home"], "draw": r[f"{prod}:p_draw"], "away": r[f"{prod}:p_away"]}
        extras = {k: r[f"goals:{k}"] for k in ("over_1_5", "over_2_5", "over_3_5", "btts")}
        b = best_pick(r["home"], r["away"], probs, extras, tuple(pc["markets"]))
        picks.append({
            "date": r["date"], "season": r["season"], "league": r["league"], "home": r["home"], "away": r["away"],
            "market": b.market, "selection": b.selection, "label": b.label, "probability": b.p,
            "won": won(b.market, b.selection, r["home_score"], r["away_score"]),
            "odds": closing_odds(b.market, b.selection, r),
            "market_probability": market_probability(b.market, b.selection, r),
        })
    p = pd.DataFrame(picks)
    p["day_rank"] = p.groupby("date")["probability"].rank(ascending=False, method="first").astype(int)
    top = p[p["day_rank"] <= pc["per_day"]]

    def by(df, col):
        return {str(k): summarise(g) for k, g in df.groupby(col)}

    bands = pd.cut(top["probability"], [0, 0.6, 0.7, 0.8, 0.9, 1.0], labels=["<60%", "60-70%", "70-80%", "80-90%", "90%+"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rule": {"markets": pc["markets"], "per_day": pc["per_day"], "model": prod},
        "seasons": sorted(p["season"].unique().tolist()),
        "all_matches": summarise(p),
        "top_per_day": summarise(top),
        "top_by_market": by(top, "market"),
        "top_by_season": by(top, "season"),
        "top_by_band": {str(k): summarise(g) for k, g in top.groupby(bands, observed=True)},
        "days": int(top["date"].nunique()),
        "days_all_won": int(top.groupby("date")["won"].all().sum()),
    }
    out = project_path(pc["backtest"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=float))

    t = report["top_per_day"]
    print(f"Top {pc['per_day']} picks per day, {report['seasons'][0]}..{report['seasons'][-1]}: "
          f"{t['n']} picks, won {t['won']} ({t['hit_rate']:.1%}) vs predicted {t['avg_probability']:.1%}")
    if "priced" in t:
        pr = t["priced"]
        print(f"  with real closing odds: {pr['n']} picks, avg odds {pr['avg_odds']:.2f}, "
              f"profit {pr['profit_units']:+.1f} units, ROI {pr['roi']:+.1%}")
    if "vs_market" in t:
        vm = t["vs_market"]
        print(f"  where the bookmaker's chance is known ({vm['n']} picks): ours {vm['ours']:.1%}, "
              f"bookmaker {vm['market']:.1%}, actually won {vm['hit_rate']:.1%}")
    print("  by market:")
    for k, v in report["top_by_market"].items():
        extra = f", ROI {v['priced']['roi']:+.1%} on {v['priced']['n']}" if "priced" in v else ""
        print(f"    {k:14} {v['n']:5} picks  won {v['hit_rate']:.1%}  predicted {v['avg_probability']:.1%}{extra}")
    print("  by confidence:")
    for k, v in report["top_by_band"].items():
        print(f"    {k:7} {v['n']:5} picks  won {v['hit_rate']:.1%}  predicted {v['avg_probability']:.1%}")
    print(f"  days where every top pick won: {report['days_all_won']} of {report['days']}")
    print(f"-> {pc['backtest']}")


if __name__ == "__main__":
    main()
