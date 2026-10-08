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


def weekly_lists_backtest(df: pd.DataFrame, prod: str, pc: dict) -> dict:
    """Each weekly list replayed over the test weeks: the same candidate rule as live, the top
    per_week by chance in each Tue-Mon week (full weeks only), settled on the real scores."""
    from predictor.markets_extra import adjust_grid
    from predictor.models.dixon_coles import MARGIN_CAP, margin_distribution, score_grid
    from predictor.picks import settle_state, stake_return, weekly_candidate

    need_margin = any(sp["kind"] == "ah" for sp in pc["weekly_lists"].values())
    rows = []
    for _, r in df.iterrows():
        probs = {"home": r[f"{prod}:p_home"], "draw": r[f"{prod}:p_draw"], "away": r[f"{prod}:p_away"]}
        extras = {k: r[f"goals:{k}"] for k in ("over_1_5", "over_2_5", "over_3_5", "btts")}
        if need_margin and pd.notna(r.get("dc_lam")):
            g = adjust_grid(score_grid(r["dc_lam"], r["dc_mu"], r["dc_rho"], 10),
                            (probs["home"], probs["draw"], probs["away"]), extras)
            extras["margin"] = {"cap": MARGIN_CAP, "probs": margin_distribution(g).tolist()}
        rows.append((r, probs, extras))
    out = {}
    for name, spec in pc["weekly_lists"].items():
        picks = []
        for r, probs, extras in rows:
            c = weekly_candidate(r["home"], r["away"], probs, extras, spec, tuple(pc["markets"]))
            if c is None:
                continue
            state = settle_state(c.market, c.selection, int(r["home_score"]), int(r["away_score"]))
            odds = closing_odds(c.market, c.selection, r)
            picks.append({"date": r["date"], "p": c.p, "market": c.market, "state": state,
                          "closing": odds, "profit": stake_return(state, odds) if odds else np.nan})
        p = pd.DataFrame(picks)
        p["week"] = pd.to_datetime(p["date"]).dt.to_period("W-MON")
        p["rank"] = p.groupby("week")["p"].rank(ascending=False, method="first")
        top = p[p["rank"] <= pc["per_week"]]
        top = top[top.groupby("week")["p"].transform("count") == pc["per_week"]]
        # a half win/loss counts half
        top = top.assign(score=top["state"].map({"won": 1, "half_won": 0.5, "push": 0.5, "half_lost": 0,
                                                  "lost": 0}).astype(float),
                         decided=~top["state"].isin(["push"]))
        by = top.groupby("week")["score"].sum()
        res = {"label": spec["label"], "weeks": int(len(by)), "n": int(len(top)),
               "hit_rate": float(top.loc[top["decided"], "score"].mean()),
               "avg_probability": float(top["p"].mean()), "avg_fair_odds": float((1 / top["p"]).mean()),
               "avg_won_per_week": float(by.mean()), "perfect_weeks": int((by == pc["per_week"]).sum()),
               "won_distribution": {str(k): int(v) for k, v in by.round().astype(int).value_counts().sort_index().items()},
               "markets": {k: int(v) for k, v in top["market"].value_counts().items()}}
        priced = top.dropna(subset=["profit"])
        if len(priced) >= 50:
            se = float(priced["profit"].std(ddof=1) / np.sqrt(len(priced)))
            res["priced"] = {"n": int(len(priced)), "avg_odds": float(priced["closing"].mean()),
                             "profit_units": float(priced["profit"].sum()), "roi": float(priced["profit"].mean()),
                             "roi_ci": [float(priced["profit"].mean() - 1.96 * se),
                                        float(priced["profit"].mean() + 1.96 * se)]}
        res["calibration_gap"] = res["hit_rate"] - res["avg_probability"]  # + = we were too cautious
        out[name] = res
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

    weekly_lists = weekly_lists_backtest(df, prod, pc)

    # weekly top-n: same Tue-Mon blocks the walk-forward predicted in (one cutoff per week)
    p["week"] = pd.to_datetime(p["date"]).dt.to_period("W-MON")
    p["week_rank"] = p.groupby("week")["probability"].rank(ascending=False, method="first").astype(int)
    wk = p[p["week_rank"] <= pc["per_week"]]
    # only full weeks (a quiet week at a season break can have fewer than 10 eligible matches)
    full = wk.groupby("week")["won"].transform("count") == pc["per_week"]
    wk = wk[full]
    wk_by = wk.groupby("week")["won"].agg(["sum", "count"])
    weekly = {**summarise(wk), "weeks": int(len(wk_by)), "perfect_weeks": int((wk_by["sum"] == wk_by["count"]).sum()),
              "avg_won_per_week": float(wk_by["sum"].mean()),
              "won_distribution": {int(k): int(v) for k, v in wk_by["sum"].value_counts().sort_index().items()}}

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
        "weekly": weekly,
        "weekly_lists": weekly_lists,
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
    print(f"Weekly top {pc['per_week']}: {weekly['n']} picks over {weekly['weeks']} weeks, won {weekly['hit_rate']:.1%} "
          f"vs predicted {weekly['avg_probability']:.1%}; avg {weekly['avg_won_per_week']:.1f}/10 per week; "
          f"all 10 won in {weekly['perfect_weeks']} weeks; distribution {weekly['won_distribution']}")
    print(f"\nWeekly lists ({pc['per_week']} per Tue-Mon week, full weeks only):")
    for name, v in weekly_lists.items():
        roi = (f", ROI at closing {v['priced']['roi']:+.1%} [{v['priced']['roi_ci'][0]:+.1%}, {v['priced']['roi_ci'][1]:+.1%}]"
               f" on {v['priced']['n']}" if v.get("priced") else "")
        print(f"  {name:8} {v['weeks']:3} weeks  avg fair @{v['avg_fair_odds']:.2f}  won {v['hit_rate']:.1%} "
              f"(predicted {v['avg_probability']:.1%})  avg {v['avg_won_per_week']:.1f}/10  "
              f"all-10 weeks {v['perfect_weeks']}{roi}")
    print(f"-> {pc['backtest']}")


if __name__ == "__main__":
    main()
