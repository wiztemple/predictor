"""Build the sport-agnostic predictions.json document."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from predictor.calibration import GOALS_KEYS, apply_goals_calibration
from predictor.handicap import rescale_margins
from predictor.models.dixon_coles import MARGIN_CAP
from predictor.models import MatchModel
from predictor.picks import best_pick, rank_by_day

SCHEMA_VERSION = "1.0"


def match_id(sport: str, league: str, kickoff: pd.Timestamp, home: str, away: str) -> str:
    raw = f"{sport}|{league}|{kickoff:%Y-%m-%d}|{home}|{away}"
    return hashlib.sha1(raw.encode()).hexdigest()[:12]


def _r(x: float, nd: int = 4) -> float:
    return round(float(x), nd)


def _probs(row) -> dict[str, float]:
    return {"home": _r(row["p_home"]), "draw": _r(row["p_draw"]), "away": _r(row["p_away"])}


def _grid(model, league: str, home: str, away: str, n: int) -> dict[str, Any]:
    g = model.grid(league, home, away)
    shown = g[: n + 1, : n + 1]
    return {"max_goals": n, "cells": np.round(shown, 4).tolist(), "other": _r(1 - shown.sum())}


def build_document(
    fixtures: pd.DataFrame,
    primary: MatchModel,
    secondary: list[MatchModel],
    unmatched: list[dict],
    league_names: dict[str, str],
    data_through: pd.Timestamp,
    status: str,
    grid_max_goals: int,
    sport: str = "football",
    goals_calibration: dict | None = None,
    pick_markets=None,
) -> dict[str, Any]:
    """fixtures: league, kickoff (UTC), home_mapped, away_mapped, source, season."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fx = fixtures.drop(columns=["home", "away"]).rename(columns={"home_mapped": "home", "away_mapped": "away"})
    fx["date"] = fx["kickoff"].dt.tz_convert(None).dt.normalize()
    model_in = fx[["league", "date", "home", "away"]]

    main = primary.predict(model_in) if len(fx) else None
    goals_calibrated = bool(goals_calibration) and main is not None and "p_over_2_5" in main.columns
    if goals_calibrated:
        keys = [k for k in GOALS_KEYS if f"p_{k}" in main.columns]
        cal = apply_goals_calibration({k: main[f"p_{k}"].to_numpy() for k in keys}, goals_calibration["markets"])
        for k in keys:
            main[f"p_{k}"] = cal[k]
    others = {m.describe(): (m, m.predict(model_in)) for m in secondary} if len(fx) else {}

    records = []
    for i, f in fx.reset_index(drop=True).iterrows():
        p = main.iloc[i]
        rec: dict[str, Any] = {
            "id": match_id(sport, f["league"], f["kickoff"], f["home"], f["away"]),
            "sport": sport,
            "league": f["league"],
            "league_name": league_names.get(f["league"], f["league"]),
            "season": f["season"],
            "kickoff": f["kickoff"].isoformat().replace("+00:00", "Z"),
            # schedules publish 00:00 UTC when the kickoff time isn't set yet
            "kickoff_tbc": bool(f["kickoff"].hour == 0 and f["kickoff"].minute == 0),
            "home": f["home"],
            "away": f["away"],
            "probabilities": _probs(p),
            "extras": {},
            "model": {"name": primary.name, "version": primary.version},
            "other_models": [
                {"name": m.name, "version": m.version, "probabilities": _probs(pred.iloc[i])}
                for m, pred in others.values()
            ],
            "fixture_source": f["source"],
            "generated_at": now,
        }
        if "p_over_2_5" in main.columns:
            rec["extras"] = {
                "expected_goals": {"home": _r(p["exp_home_goals"], 2), "away": _r(p["exp_away_goals"], 2)},
                "over_1_5": _r(p["p_over_1_5"]),
                "over_2_5": _r(p["p_over_2_5"]),
                "over_3_5": _r(p["p_over_3_5"]),
                "btts": _r(p["p_btts"]),
                "top_scorelines": [{**s, "p": _r(s["p"])} for s in p["top_scorelines"]],
            }
            if "margin_probs" in main.columns and p["margin_probs"] is not None:
                # goal-difference chances, rescaled so AH -0.5 / 0 agree with the published 1X2
                m = rescale_margins(np.asarray(p["margin_probs"]), p["p_home"], p["p_draw"], p["p_away"])
                rec["extras"]["margin"] = {"cap": MARGIN_CAP, "probs": [round(float(v), 5) for v in m]}
            rec["extras"]["goals_model"] = "dixon_coles"
            # over/under and BTTS are calibrated; expected goals and the scoreline grid are the raw model
            rec["extras"]["goals_calibrated"] = goals_calibrated
            if hasattr(primary, "grid"):
                rec["extras"]["score_grid"] = _grid(primary, f["league"], f["home"], f["away"], grid_max_goals)
        records.append(rec)

    # cross-market best pick per match + its rank within the UK day (the tracked rule)
    if records and pick_markets:
        bp = [best_pick(r["home"], r["away"], r["probabilities"], r["extras"], tuple(pick_markets)) for r in records]
        ranks = rank_by_day(pd.DataFrame({"kickoff": [r["kickoff"] for r in records],
                                          "probability": [b.p if b else -1.0 for b in bp]}))
        for r, b, k in zip(records, bp, ranks):
            if b is not None:
                r["best_pick"] = {"market": b.market, "selection": b.selection, "label": b.label,
                                  "p": _r(b.p), "day_rank": int(k)}

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now,
        "status": status,
        "data_through": f"{data_through:%Y-%m-%d}",
        "leagues": [{"code": c, "name": n, "sport": sport} for c, n in league_names.items()],
        "predictions": records,
        "unmatched": unmatched,
    }
