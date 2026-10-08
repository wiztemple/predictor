"""Append-only prediction log and live scoring.

Honesty rules:
  * Only fixtures that haven't kicked off are logged, stamped with logged_at.
  * The log is append-only (monthly JSONL files). Re-runs that produce the same
    numbers are not re-logged; changed numbers are logged as a new entry.
  * A match is scored with the LATEST entry logged before its kickoff.
  * A logged fixture is matched to a result only if the match was played within
    `date_tolerance_days` of the logged kickoff; postponed fixtures are void
    (a fresh prediction gets logged before the rearranged date).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictor.metrics import odds_to_probs, score

def _summary(rec: dict) -> dict:
    x = rec.get("extras") or {}
    return {k: x[k] for k in ("over_1_5", "over_2_5", "over_3_5", "btts", "expected_goals") if k in x}


def _entry(rec: dict, status: str, logged_at: str) -> dict[str, Any]:
    return {
        "logged_at": logged_at,
        "id": rec["id"], "sport": rec["sport"], "league": rec["league"], "season": rec["season"],
        "kickoff": rec["kickoff"], "home": rec["home"], "away": rec["away"],
        "model": rec["model"], "probabilities": rec["probabilities"],
        "extras_summary": _summary(rec),
        "other_models": rec.get("other_models", []),
        "status": status,
    }


def load_log(log_dir: Path) -> list[dict]:
    entries = []
    for f in sorted(Path(log_dir).glob("*.jsonl")):
        with open(f) as fh:
            entries.extend(json.loads(line) for line in fh if line.strip())
    return entries


def _same(a: dict, b: dict) -> bool:
    return (a["model"] == b["model"] and a["probabilities"] == b["probabilities"]
            and a["kickoff"] == b["kickoff"] and a["extras_summary"] == b["extras_summary"])


def log_predictions(doc: dict, log_dir: Path, now: datetime) -> tuple[int, int]:
    """Append not-yet-kicked-off predictions from a predictions.json document.

    Returns (appended, skipped_unchanged). `now` must be timezone-aware UTC.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    last: dict[tuple, dict] = {}
    for e in load_log(log_dir):
        last[(e["id"], e["model"]["name"])] = e  # files are chronological -> keeps latest
    logged_at = now.isoformat(timespec="seconds").replace("+00:00", "Z")
    new, skipped = [], 0
    for rec in doc["predictions"]:
        if pd.Timestamp(rec["kickoff"]) <= pd.Timestamp(now):
            continue
        entry = _entry(rec, doc.get("status", "unknown"), logged_at)
        prev = last.get((rec["id"], rec["model"]["name"]))
        if prev is not None and _same(prev, entry):
            skipped += 1
            continue
        new.append(entry)
    if new:
        with open(log_dir / f"{now:%Y-%m}.jsonl", "a") as fh:
            for e in new:
                fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    return len(new), skipped


def official_predictions(entries: list[dict]) -> pd.DataFrame:
    """Latest entry logged strictly before kickoff, per (match id, model)."""
    if not entries:
        return pd.DataFrame()
    df = pd.DataFrame(entries)
    df["logged_at_ts"] = pd.to_datetime(df["logged_at"], utc=True)
    df["kickoff_ts"] = pd.to_datetime(df["kickoff"], utc=True)
    df = df[df["logged_at_ts"] < df["kickoff_ts"]]
    df["model_name"] = df["model"].map(lambda m: m["name"])
    # whole-row "last" (groupby().last() would mix non-null values across rows)
    df = df.sort_values("logged_at_ts", kind="stable").drop_duplicates(["id", "model_name"], keep="last")
    for k in ("home", "draw", "away"):
        df[f"p_{k}"] = df["probabilities"].map(lambda p, k=k: p[k])
    return df


def attach_results(official: pd.DataFrame, matches: pd.DataFrame, now: datetime,
                   date_tolerance_days: int = 1, void_after_days: int = 3) -> pd.DataFrame:
    """Adds state (scored / pending / void), outcome, scores and bookmaker probabilities."""
    if official.empty:
        return official
    res = matches[["league", "home", "away", "date", "home_score", "away_score", "outcome",
                   "odds_home", "odds_draw", "odds_away"]]
    m = official.merge(res, on=["league", "home", "away"], how="left", suffixes=("", "_res"))
    kick_day = m["kickoff_ts"].dt.tz_convert("Europe/London").dt.tz_localize(None).dt.normalize()
    close = (m["date"] - kick_day).abs() <= pd.Timedelta(days=date_tolerance_days)
    m.loc[~close, ["date", "home_score", "away_score", "outcome", "odds_home", "odds_draw", "odds_away"]] = np.nan
    # one row per prediction: prefer the matched result
    m["_has"] = m["outcome"].notna()
    m = (m.sort_values("_has", kind="stable").drop_duplicates(["id", "model_name"], keep="last")
         .drop(columns="_has").reset_index(drop=True))
    age = pd.Timestamp(now) - m["kickoff_ts"]
    m["state"] = np.where(m["outcome"].notna(), "scored",
                          np.where(age > pd.Timedelta(days=void_after_days), "void", "pending"))
    has_odds = m[["odds_home", "odds_draw", "odds_away"]].notna().all(axis=1)
    bk = np.full((len(m), 3), np.nan)
    if has_odds.any():
        bk[has_odds.to_numpy()] = odds_to_probs(m.loc[has_odds, "odds_home"], m.loc[has_odds, "odds_draw"],
                                                m.loc[has_odds, "odds_away"])
    m[["bk_p_home", "bk_p_draw", "bk_p_away"]] = bk
    return m


def live_summary(scored: pd.DataFrame, primary_model: str, recent: int = 40) -> dict[str, Any]:
    if scored.empty:
        return {"n_logged_matches": 0, "n_scored": 0, "n_pending": 0, "n_void": 0, "recent": []}
    prim = scored[scored["model_name"] == primary_model]
    done = prim[prim["state"] == "scored"]
    out: dict[str, Any] = {
        "primary_model": primary_model,
        "first_logged": prim["logged_at_ts"].min().isoformat() if len(prim) else None,
        "n_logged_matches": int(len(prim)),
        "n_scored": int(len(done)),
        "n_pending": int((prim["state"] == "pending").sum()),
        "n_void": int((prim["state"] == "void").sum()),
    }
    if len(done):
        out["model"] = score(done)
        with_odds = done.dropna(subset=["bk_p_home"])
        if len(with_odds):
            out["same_matches_with_odds"] = {
                "n": int(len(with_odds)),
                "model": score(with_odds),
                "bookmaker": score(with_odds, ["bk_p_home", "bk_p_draw", "bk_p_away"]),
            }
        by_league = {lg: score(g) for lg, g in done.groupby("league")}
        out["by_league"] = by_league
    rows = prim.sort_values("kickoff_ts", ascending=False).head(recent)
    out["recent"] = [
        {
            "id": r.id, "league": r.league, "kickoff": r.kickoff, "home": r.home, "away": r.away,
            "logged_at": r.logged_at, "probabilities": r.probabilities, "state": r.state,
            "score": None if r.state != "scored" else f"{int(r.home_score)}-{int(r.away_score)}",
            "outcome": None if r.state != "scored" else r.outcome,
        }
        for r in rows.itertuples()
    ]
    for k in ("model", "same_matches_with_odds", "by_league"):
        if k in out:
            out[k] = json.loads(json.dumps(out[k], default=float))
    return out
