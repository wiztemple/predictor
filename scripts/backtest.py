#!/usr/bin/env python
"""Step 3: walk-forward backtest, benchmark against the bookmaker, calibration.

Protocol (fixed before looking at test results):
  * Walk-forward predictions from evaluation.oos_from_season onward; each week is
    predicted by models fitted only on earlier matches.
  * Everything that is chosen - blend weight, calibration method, production
    model - is chosen on seasons BEFORE the test period.
  * In the test period, each season's calibrator is fitted on all out-of-sample
    predictions from earlier seasons only.
  * Bookmaker benchmark: closing odds with the margin removed proportionally.

Writes data/backtest/{predictions.parquet, summary.json, report.md}.

    python scripts/backtest.py            # reuses cached walk-forward predictions
    python scripts/backtest.py --refresh  # recompute them
"""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from predictor.backtest import walk_forward
from predictor.calibration import (
    BINARY_CALIBRATORS,
    CALIBRATORS,
    GOALS_KEYS,
    apply_goals_calibration,
    expected_calibration_error,
    reliability_table,
)
from predictor.config import load_config, project_path
from predictor.handicap import fair_odds, home_outcome, main_line, rescale_margins
from predictor.models.dixon_coles import MARGIN_CAP
from predictor.features import form_features, involves_promoted_team
from predictor.metrics import (
    binary_reliability,
    binary_scores,
    cluster_bootstrap_mean,
    odds_to_probs,
    per_match_log_loss,
    score,
)
from predictor.models import get_model
from predictor.stacking import BASE_FEATURES, ODDS_FEATURES, walk_forward_gbm

P = ["p_home", "p_draw", "p_away"]
BASES = ["elo", "dixon_coles", "blend"]
LABEL = {
    "bookmaker": "Bookmaker (closing, margin removed)",
    "elo": "Elo", "dixon_coles": "Dixon-Coles", "blend": "Elo + Dixon-Coles blend",
    "gbm": "Gradient boosting (no odds)", "gbm_odds": "Gradient boosting (with odds)",
}


def cols(prefix: str) -> list[str]:
    return [f"{prefix}_{c}" for c in P]


def build_table(matches: pd.DataFrame, refresh: bool, out_dir, freq: str, from_season: str) -> pd.DataFrame:
    """One row per out-of-sample match with all base-model outputs and features."""
    mask = matches["season"] >= from_season
    t = matches[mask].copy()
    for name, prefix in (("elo", "elo"), ("dixon_coles", "dc")):
        cache = out_dir / f"wf_{name}.parquet"
        if refresh or not cache.exists():
            print(f"walk-forward {name} from {from_season} ...", flush=True)
            wf = walk_forward(get_model(name), matches, mask, freq)
            wf.drop(columns=["top_scorelines"], errors="ignore").to_parquet(cache, index=False)
        wf = pd.read_parquet(cache).set_index("match_idx")
        keep = [c for c in ["p_home", "p_draw", "p_away", "elo_diff", "exp_home_goals", "exp_away_goals",
                            "p_over_1_5", "p_over_2_5", "p_over_3_5", "p_btts", "margin_probs"] if c in wf]
        renamed = wf[keep].rename(columns=lambda c: c if c == "elo_diff" else f"{prefix}_{c}")
        t = t.join(renamed)
        if prefix == "elo":
            t["cutoff"] = wf["cutoff"]
    t[cols("bk")] = odds_to_probs(t["odds_home"], t["odds_draw"], t["odds_away"])
    t = t.join(form_features(matches).loc[t.index])
    t["promoted"] = involves_promoted_team(matches).loc[t.index]
    assert t[cols("elo") + cols("dc")].notna().all().all(), "missing walk-forward predictions"
    return t


def ll(t: pd.DataFrame, c: list[str]) -> float:
    return score(t, c)["log_loss"]


def calibrate_expanding(t: pd.DataFrame, src: list[str], method: str, seasons: list[str]) -> np.ndarray:
    """For each season in `seasons`, fit on all earlier rows; returns probs for those seasons' rows."""
    out = np.full((len(t), 3), np.nan)
    for s in seasons:
        fit_rows, apply_rows = t["season"] < s, t["season"] == s
        cal = CALIBRATORS[method]().fit(t.loc[fit_rows, src].to_numpy(), t.loc[fit_rows, "outcome"])
        out[apply_rows.to_numpy()] = cal.transform(t.loc[apply_rows, src].to_numpy())
    return out


def goals_section(t, test, matches, ev, test_seasons, holdout, out_dir, say) -> dict:
    """Goals markets: pre-test choice of calibration, expanding calibration in the test
    period, bookmaker over/under 2.5 benchmark, and the production calibrators."""
    total = matches["home_score"] + matches["away_score"]
    yes_all = {
        "over_1_5": total >= 2, "over_2_5": total >= 3, "over_3_5": total >= 4,
        "btts": (matches["home_score"] >= 1) & (matches["away_score"] >= 1),
    }
    y = {k: v.loc[t.index].astype(int).to_numpy() for k, v in yes_all.items()}
    raw = {k: t[f"dc_p_{k}"].to_numpy() for k in GOALS_KEYS}
    season = t["season"].to_numpy()
    is_test = np.isin(season, test_seasons)

    # 1. choice per market on the pre-test holdout season
    say("\n## 4. Goals markets (Dixon-Coles)\n")
    say(f"Calibration choice: fitted on {ev['oos_from_season']}..{holdout} (exclusive), scored on {holdout}. "
        "Log loss:\n")
    say("| market | none | platt | isotonic | chosen |")
    say("|---|---|---|---|---|")
    fit_m, hold_m = season < holdout, season == holdout
    choice = {}
    for k in GOALS_KEYS:
        res = {}
        for name, cls in BINARY_CALIBRATORS.items():
            cal = cls().fit(raw[k][fit_m], y[k][fit_m])
            res[name] = binary_scores(cal.transform(raw[k][hold_m]), y[k][hold_m])["log_loss"]
        choice[k] = min(res, key=res.get)
        say(f"| {k} | {res['none']:.4f} | {res['platt']:.4f} | {res['isotonic']:.4f} | **{choice[k]}** |")

    # 2. test period: each season calibrated on all earlier seasons only
    cal = {k: raw[k].copy() for k in GOALS_KEYS}
    for s in test_seasons:
        prior, rows = season < s, season == s
        if not rows.any():
            continue
        cals = {k: BINARY_CALIBRATORS[choice[k]]().fit(raw[k][prior], y[k][prior]).to_dict() for k in GOALS_KEYS}
        out = apply_goals_calibration({k: raw[k][rows] for k in GOALS_KEYS}, cals)
        for k in GOALS_KEYS:
            cal[k][rows] = out[k]

    # baseline: league rate over all earlier seasons
    hist = pd.DataFrame({"league": matches["league"], "season": matches["season"]})
    base = {k: np.empty(int(is_test.sum())) for k in GOALS_KEYS}
    tt = t[is_test]
    for (lg, s), idx in tt.groupby(["league", "season"]).groups.items():
        prior = (hist["league"] == lg) & (hist["season"] < s)
        pos = tt.index.get_indexer(idx)
        for k in GOALS_KEYS:
            base[k][pos] = yes_all[k][prior].mean()

    # bookmaker over/under 2.5, margin removed
    inv_o, inv_u = 1 / tt["odds_over_2_5"].to_numpy(), 1 / tt["odds_under_2_5"].to_numpy()
    bk_over = inv_o / (inv_o + inv_u)
    has_bk = np.isfinite(bk_over)

    say(f"\nTest period ({int(is_test.sum())} matches). Log loss (lower is better):\n")
    say("| market | baseline | model raw | model calibrated | bookmaker | calibration error raw -> calibrated |")
    say("|---|---|---|---|---|---|")
    goals = {}
    clusters = tt["cutoff"].to_numpy()
    for k in GOALS_KEYS:
        yt, rt, ct = y[k][is_test], raw[k][is_test], cal[k][is_test]
        rel_raw, rel_cal = binary_reliability(rt, yt), binary_reliability(ct, yt)
        ece = lambda r: float(np.average((r["mean_pred"] - r["observed"]).abs(), weights=r["n"]))  # noqa: E731
        entry = {
            "calibration": choice[k],
            "model_raw": binary_scores(rt, yt), "model": binary_scores(ct, yt), "baseline": binary_scores(base[k], yt),
            "ece_raw": ece(rel_raw), "ece": ece(rel_cal), "base_rate": float(yt.mean()),
            "reliability": rel_cal.round(4).to_dict(orient="records"),
        }
        bk_txt = "-"
        if k == "over_2_5":
            m_, b_ = binary_scores(ct[has_bk], yt[has_bk]), binary_scores(bk_over[has_bk], yt[has_bk])
            d = (_binary_ll(ct[has_bk], yt[has_bk]) - _binary_ll(bk_over[has_bk], yt[has_bk]))
            mean, lo, hi = cluster_bootstrap_mean(d, clusters[has_bk])
            entry["bookmaker"] = {"n": int(has_bk.sum()), "model": m_, "bookmaker": b_,
                                  "gap": {"mean": mean, "ci_low": lo, "ci_high": hi},
                                  "ece_bookmaker": ece(binary_reliability(bk_over[has_bk], yt[has_bk]))}
            bk_txt = f"{b_['log_loss']:.4f}"
        thresholds = []
        for direction, q in (("over", ct), ("under", 1 - ct)):
            hit = yt if direction == "over" else 1 - yt
            for t_ in (0.5, 0.6, 0.7, 0.8):
                sel = q >= t_
                if sel.sum():
                    thresholds.append({"direction": direction, "min_p": t_, "n": int(sel.sum()),
                                       "mean_pred": float(q[sel].mean()), "hit_rate": float(hit[sel].mean())})
        entry["thresholds"] = thresholds
        goals[k] = entry
        say(f"| {k} | {entry['baseline']['log_loss']:.4f} | {entry['model_raw']['log_loss']:.4f} | "
            f"{entry['model']['log_loss']:.4f} | {bk_txt} | {entry['ece_raw']:.4f} -> {entry['ece']:.4f} |")

    b = goals["over_2_5"]["bookmaker"]
    say(f"\nOver/under 2.5 vs bookmaker on {b['n']} matches: model {b['model']['log_loss']:.4f}, bookmaker "
        f"{b['bookmaker']['log_loss']:.4f}, gap {b['gap']['mean']:+.4f} [{b['gap']['ci_low']:+.4f}, {b['gap']['ci_high']:+.4f}]")
    say("\nCalibrated: when the model gave at least X%, how often did it happen?\n")
    say("| market | side | min | n | avg predicted | happened |")
    say("|---|---|---|---|---|---|")
    for k, g in goals.items():
        for t_ in g["thresholds"]:
            say(f"| {k} | {t_['direction']} | {t_['min_p']:.0%} | {t_['n']} | {t_['mean_pred']:.1%} | {t_['hit_rate']:.1%} |")

    # 3. production calibrators: chosen method, fitted on ALL out-of-sample predictions so far
    prod = {k: BINARY_CALIBRATORS[choice[k]]().fit(raw[k], y[k]).to_dict() for k in GOALS_KEYS}
    model_dir = out_dir.parent / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "goals_calibration.json").write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fitted_on": {"from_season": ev["oos_from_season"], "through": f"{t['date'].max():%Y-%m-%d}", "n": int(len(t))},
        "markets": prod,
    }, indent=1))
    say(f"\nProduction calibrators ({choice}) fitted on {len(t)} out-of-sample matches -> data/models/goals_calibration.json")
    # calibrated test-period probabilities, as they would have been shown at the time
    return goals, pd.DataFrame({k: cal[k][is_test] for k in GOALS_KEYS}, index=tt.index)


def ah_section(test: pd.DataFrame, prob_cols: list[str], say) -> dict:
    """Asian handicap at each match's main line: predicted vs actual win/push/lose (home side),
    plus average profit per unit staked at our own fair odds (0 = perfectly calibrated)."""
    rows = []
    for (_, r), (ph, pd_, pa) in zip(test.iterrows(), test[prob_cols].to_numpy()):
        mp = r.get("dc_margin_probs")
        if mp is None or (isinstance(mp, float) and np.isnan(mp)):
            continue
        m = rescale_margins(np.asarray(mp, float), ph, pd_, pa)
        line = main_line(m)
        w, p, l = home_outcome(m, line)
        actual = np.zeros(2 * MARGIN_CAP + 1)
        actual[int(np.clip(r["home_score"] - r["away_score"], -MARGIN_CAP, MARGIN_CAP)) + MARGIN_CAP] = 1
        aw, ap, al = home_outcome(actual, line)
        for side, (pw, pp, pl), (xw, xp, xl) in (("home", (w, p, l), (aw, ap, al)), ("away", (l, p, w), (al, ap, aw))):
            o = fair_odds(pw, pl)
            rows.append({"side": side, "line": line, "chance": 1 / o, "pw": pw, "pp": pp, "pl": pl,
                         "aw": xw, "ap": xp, "al": xl, "profit_at_fair": xw * (o - 1) - xl})
    df = pd.DataFrame(rows)
    home = df[df["side"] == "home"]
    out = {
        "n_matches": int(len(home)),
        "predicted": {"win": float(home["pw"].mean()), "push": float(home["pp"].mean()), "lose": float(home["pl"].mean())},
        "actual": {"win": float(home["aw"].mean()), "push": float(home["ap"].mean()), "lose": float(home["al"].mean())},
        "profit_at_fair": float(df["profit_at_fair"].mean()),
    }
    bands = pd.cut(df["chance"], [0, 0.45, 0.5, 0.55, 0.6, 1.0], labels=["<45%", "45-50%", "50-55%", "55-60%", "60%+"])
    out["by_chance"] = {
        str(k): {"n": int(len(g)), "chance": float(g["chance"].mean()),
                 "won": float(g["aw"].mean()), "push": float(g["ap"].mean()), "lost": float(g["al"].mean()),
                 "profit_at_fair": float(g["profit_at_fair"].mean())}
        for k, g in df.groupby(bands, observed=True)
    }
    say("\n## 5. Asian handicap (main line), test period\n")
    say(f"{out['n_matches']} matches. Home side, stake-weighted: predicted win/push/lose "
        f"{out['predicted']['win']:.1%} / {out['predicted']['push']:.1%} / {out['predicted']['lose']:.1%}, actual "
        f"{out['actual']['win']:.1%} / {out['actual']['push']:.1%} / {out['actual']['lose']:.1%}.")
    say(f"Average profit per unit at our own fair odds: {out['profit_at_fair']:+.3f} (0 = calibrated; "
        "negative = we were too optimistic). No bookmaker AH benchmark yet.\n")
    say("| our chance | bets | avg chance | won | push | lost | profit at fair odds |")
    say("|---|---|---|---|---|---|---|")
    for k, v in out["by_chance"].items():
        say(f"| {k} | {v['n']} | {v['chance']:.1%} | {v['won']:.1%} | {v['push']:.1%} | {v['lost']:.1%} | {v['profit_at_fair']:+.3f} |")
    return out


def _binary_ll(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-15, 1 - 1e-15)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def main() -> None:
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    ev = cfg["evaluation"]
    out_dir = project_path("data/backtest")
    out_dir.mkdir(parents=True, exist_ok=True)
    matches = pd.read_parquet(project_path(cfg["paths"]["matches"]))
    t = build_table(matches, args.refresh, out_dir, ev["refit_frequency"], ev["oos_from_season"])

    test_seasons = ev["test_seasons"]
    holdout = ev["selection_holdout_season"]
    pre = t[~t["season"].isin(test_seasons)]
    assert pre["season"].max() < min(test_seasons)
    lines: list[str] = []
    say = lambda s="": (print(s), lines.append(s))  # noqa: E731

    # ---------------- 1. pre-test selection --------------------------------------
    say("# Backtest report\n")
    say(f"Out-of-sample predictions from {ev['oos_from_season']}; test seasons {', '.join(test_seasons)}.")
    say(f"All choices below were made on seasons before {min(test_seasons)}.\n")
    say("## 1. Choices made on pre-test data\n")

    tune = pre[pre["season"].isin(ev["tune_seasons"])]
    weights = np.round(np.linspace(0, 1, 11), 2)
    blend_ll = {w: ll(tune.assign(**{c: w * tune[f"elo_{c}"] + (1 - w) * tune[f"dc_{c}"] for c in P}), P)
                for w in weights}
    w_elo = min(blend_ll, key=blend_ll.get)
    say(f"Blend weight on Elo (tune seasons {ev['tune_seasons']}): **{w_elo}** "
        f"(log loss {blend_ll[w_elo]:.4f}; Elo only {blend_ll[1.0]:.4f}, Dixon-Coles only {blend_ll[0.0]:.4f})")
    for c in P:
        t[f"blend_{c}"] = w_elo * t[f"elo_{c}"] + (1 - w_elo) * t[f"dc_{c}"]
    pre = t[~t["season"].isin(test_seasons)]

    # GBM out-of-sample on the holdout season (trained on earlier rows only)
    train_mask = t["season"] >= ev["oos_from_season"]
    gbm_hold = walk_forward_gbm(t, BASE_FEATURES, t["season"] == holdout, train_mask)
    hold = pre[pre["season"] == holdout].copy()
    hold[cols("gbm")] = gbm_hold.loc[hold.index, P].to_numpy()

    say(f"\nCalibration choice: calibrators fitted on {ev['oos_from_season']}..{holdout} (exclusive), "
        f"scored on {holdout} ({len(hold)} matches). Log loss:\n")
    say("| base | none | isotonic | platt |")
    say("|---|---|---|---|")
    choice: dict[str, str] = {}
    hold_scores: dict[str, float] = {}
    fit_part = pre[pre["season"] < holdout]
    for base in BASES:
        src = cols({"elo": "elo", "dixon_coles": "dc", "blend": "blend"}[base])
        res = {}
        for method, cls in CALIBRATORS.items():
            cal = cls().fit(fit_part[src].to_numpy(), fit_part["outcome"])
            p = cal.transform(hold[src].to_numpy())
            res[method] = score(pd.DataFrame(p, columns=P).assign(outcome=hold["outcome"].to_numpy()))["log_loss"]
        choice[base] = min(res, key=res.get)
        hold_scores[base] = res[choice[base]]
        say(f"| {LABEL[base]} | {res['none']:.4f} | {res['isotonic']:.4f} | {res['platt']:.4f} |")
    hold_scores["gbm"] = ll(hold, cols("gbm"))
    say(f"\nGradient boosting (no odds), {holdout}: {hold_scores['gbm']:.4f}")
    say(f"Bookmaker, {holdout}: {ll(hold, cols('bk')):.4f}")
    production = min(hold_scores, key=hold_scores.get)
    say(f"\nChosen calibration per base: {choice}")
    say(f"**Pre-registered production model: {LABEL[production]}"
        f"{'' if production == 'gbm' else f' (calibration: {choice[production]})'}**\n")

    # ---------------- 2. test-period predictions ---------------------------------
    test = t[t["season"].isin(test_seasons)].copy()
    variants: dict[str, list[str]] = {"bookmaker": cols("bk")}
    for base in BASES:
        prefix = {"elo": "elo", "dixon_coles": "dc", "blend": "blend"}[base]
        variants[base] = cols(prefix)
        if choice[base] != "none":
            cal = calibrate_expanding(t, cols(prefix), choice[base], test_seasons)
            test[cols(f"{prefix}_cal")] = cal[t["season"].isin(test_seasons).to_numpy()]
            variants[f"{base}+{choice[base]}"] = cols(f"{prefix}_cal")
    print("walk-forward gradient boosting on test period ...", flush=True)
    test_mask = t["season"].isin(test_seasons)
    test[cols("gbm")] = walk_forward_gbm(t, BASE_FEATURES, test_mask, train_mask).loc[test.index, P].to_numpy()
    test[cols("gbm_odds")] = walk_forward_gbm(t, BASE_FEATURES + ODDS_FEATURES, test_mask, train_mask).loc[test.index, P].to_numpy()
    variants["gbm"] = cols("gbm")
    variants["gbm_odds"] = cols("gbm_odds")
    prod_key = production if production == "gbm" or choice[production] == "none" else f"{production}+{choice[production]}"

    def label(v: str) -> str:
        base, _, cal = v.partition("+")
        return LABEL[base] + (f" + {cal.capitalize()} calibration" if cal else "")

    # ---------------- 3. results ---------------------------------------------------
    say(f"## 2. Test period: {', '.join(test_seasons)} ({len(test)} matches)\n")
    say("Overall (lower log loss / Brier is better):\n")
    say("| model | log loss | Brier | accuracy |")
    say("|---|---|---|---|")
    rows = []
    for v, c in variants.items():
        s = score(test, c)
        say(f"| {label(v)}{' **(production)**' if v == prod_key else ''} | {s['log_loss']:.4f} | {s['brier']:.4f} | {s['accuracy']:.1%} |")
        rows.append({"model": v, "label": label(v), "league": "ALL", **s})
        for lg, g in test.groupby("league"):
            rows.append({"model": v, "label": label(v), "league": lg, **score(g, c)})
    res = pd.DataFrame(rows)

    say("\nLog loss by league:\n")
    piv = res.pivot(index="league", columns="model", values="log_loss")[list(variants)]
    say("| league | " + " | ".join(variants) + " |")
    say("|---" * (len(variants) + 1) + "|")
    for lg, r in piv.iterrows():
        say(f"| {lg} | " + " | ".join(f"{x:.4f}" for x in r) + " |")

    say("\nLog loss by season:\n")
    say("| season | n | " + " | ".join(variants) + " |")
    say("|---" * (len(variants) + 2) + "|")
    for s, g in test.groupby("season"):
        say(f"| {s} | {len(g)} | " + " | ".join(f"{ll(g, c):.4f}" for c in variants.values()) + " |")

    say("\nGap to the bookmaker (model minus bookmaker log loss; negative = model better), "
        "95% CI from a bootstrap over weeks:\n")
    bk_ll = per_match_log_loss(test[cols("bk")].to_numpy(), test["outcome"])
    gaps = {}
    for v, c in variants.items():
        if v == "bookmaker":
            continue
        d = per_match_log_loss(test[c].to_numpy(), test["outcome"]) - bk_ll
        m, lo, hi = cluster_bootstrap_mean(d, test["cutoff"])
        gaps[v] = (m, lo, hi)
        say(f"- {label(v)}: {m:+.4f}  [{lo:+.4f}, {hi:+.4f}]")

    say("\nBy bookmaker odds source (the benchmark is weaker where Pinnacle closing odds are missing):\n")
    say("| odds source | n | bookmaker | " + label(prod_key) + " | gap |")
    say("|---|---|---|---|---|")
    for src, g in test.groupby("odds_source"):
        a, b = ll(g, cols("bk")), ll(g, variants[prod_key])
        say(f"| {src} | {len(g)} | {a:.4f} | {b:.4f} | {b - a:+.4f} |")

    say("\nMatches involving a newly promoted team:\n")
    say("| subset | n | bookmaker | Elo | Dixon-Coles | " + label(prod_key) + " |")
    say("|---|---|---|---|---|---|")
    for flag, g in test.groupby("promoted"):
        say(f"| {'promoted team' if flag else 'others'} | {len(g)} | {ll(g, cols('bk')):.4f} | "
            f"{ll(g, cols('elo')):.4f} | {ll(g, cols('dc')):.4f} | {ll(g, variants[prod_key]):.4f} |")

    # ---------------- 4. calibration ----------------------------------------------
    say("\n## 3. Calibration on the test period\n")
    say("Expected calibration error (count-weighted |predicted - observed|, 10 bins):\n")
    say("| model | home | draw | away |")
    say("|---|---|---|---|")
    reliability = {}
    for v in dict.fromkeys(["bookmaker", "dixon_coles", "elo", prod_key]):
        tab = reliability_table(test[variants[v]].to_numpy(), test["outcome"])
        reliability[v] = tab
        e = expected_calibration_error(tab)
        say(f"| {label(v)} | {e['home']:.4f} | {e['draw']:.4f} | {e['away']:.4f} |")
    say(f"\nReliability table, {label(prod_key)} (bins with n >= 30):\n")
    say("| outcome | bin | n | mean predicted | observed |")
    say("|---|---|---|---|---|")
    for _, r in reliability[prod_key].query("n >= 30").iterrows():
        say(f"| {r.outcome} | {r.bin_lo:.1f}-{r.bin_hi:.1f} | {r.n} | {r.mean_pred:.3f} | {r.observed:.3f} |")

    # ---------------- 4b. goals markets (Dixon-Coles) -------------------------------
    goals, goals_test = goals_section(t, test, matches, ev, test_seasons, holdout, out_dir, say)
    ah = ah_section(test, variants[prod_key], say)

    # ---------------- 5. outputs ---------------------------------------------------
    keep = ["league", "season", "date", "home", "away", "outcome", "odds_source", "promoted", "cutoff"]
    pred_out = test[keep].copy()
    for v, c in variants.items():
        pred_out[[f"{v}:{x}" for x in P]] = test[c].to_numpy()
    for k in GOALS_KEYS:
        pred_out[f"goals:{k}"] = goals_test.loc[test.index, k].to_numpy()
    pred_out[["home_score", "away_score", "odds_home", "odds_draw", "odds_away", "odds_over_2_5", "odds_under_2_5"]] = \
        test[["home_score", "away_score", "odds_home", "odds_draw", "odds_away", "odds_over_2_5", "odds_under_2_5"]].to_numpy()
    pred_out.to_parquet(out_dir / "predictions.parquet")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "test_seasons": test_seasons,
        "n_matches": int(len(test)),
        "production_model": prod_key,
        "selection": {"blend_weight_elo": float(w_elo), "calibration": choice, "holdout_season": holdout},
        "rows": res.round(5).to_dict(orient="records"),
        "gap_to_bookmaker": {k: {"mean": round(m, 5), "ci_low": round(lo, 5), "ci_high": round(hi, 5)}
                             for k, (m, lo, hi) in gaps.items()},
        "reliability": {k: v.round(4).to_dict(orient="records") for k, v in reliability.items()},
        "labels": {v: label(v) for v in variants},
        "goals_markets": goals,
        "asian_handicap": ah,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    (out_dir / "report.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {out_dir}/summary.json, report.md, predictions.parquet")


if __name__ == "__main__":
    main()
