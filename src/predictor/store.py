"""Pick tracking database (any SQLAlchemy URL; Postgres in production, SQLite locally).

Tables
  picks_log       append-only: every pick logged before kickoff (never updated)
  official_picks  one row per match once it is settled: the LATEST pick logged
                  before kickoff, with the result, won/lost/void and closing prices

All timestamps are stored as naive UTC.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, Index, Integer, MetaData, String, Table, create_engine, func, select,
)
from sqlalchemy.engine import Engine

from predictor.config import load_env
from predictor.picks import best_pick, closing_odds, market_probability, rank_by_day, won

meta = MetaData()

picks_log = Table(
    "picks_log", meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("logged_at", DateTime, nullable=False),
    Column("match_id", String(32), nullable=False),
    Column("sport", String(16), nullable=False),
    Column("league", String(16), nullable=False),
    Column("season", String(16), nullable=False),
    Column("kickoff", DateTime, nullable=False),
    Column("home", String(80), nullable=False),
    Column("away", String(80), nullable=False),
    Column("market", String(24), nullable=False),
    Column("selection", String(16), nullable=False),
    Column("label", String(200), nullable=False),
    Column("probability", Float, nullable=False),
    Column("day", Date, nullable=False),
    Column("day_rank", Integer, nullable=False),
    Column("model", String(40), nullable=False),
    Column("status", String(16), nullable=False),
    Index("ix_picks_log_match", "match_id", "logged_at"),
)

official_picks = Table(
    "official_picks", meta,
    Column("match_id", String(32), primary_key=True),
    Column("logged_at", DateTime, nullable=False),
    Column("sport", String(16), nullable=False),
    Column("league", String(16), nullable=False),
    Column("season", String(16), nullable=False),
    Column("kickoff", DateTime, nullable=False),
    Column("home", String(80), nullable=False),
    Column("away", String(80), nullable=False),
    Column("market", String(24), nullable=False),
    Column("selection", String(16), nullable=False),
    Column("label", String(200), nullable=False),
    Column("probability", Float, nullable=False),
    Column("day", Date, nullable=False),
    Column("day_rank", Integer, nullable=False),
    Column("state", String(8), nullable=False),          # won / lost / void
    Column("won", Boolean, nullable=True),
    Column("home_score", Integer, nullable=True),
    Column("away_score", Integer, nullable=True),
    Column("closing_odds", Float, nullable=True),        # real closing odds where the data has them
    Column("market_probability", Float, nullable=True),  # bookmaker's implied chance, margin removed
    Column("settled_at", DateTime, nullable=False),
)


def database_url(cfg: dict, project_root: Path) -> str:
    load_env(project_root / ".env")
    url = os.environ.get(cfg.get("database_url_env", "DATABASE_URL"))
    if not url and os.environ.get("GITHUB_ACTIONS") == "true":
        # On CI a local SQLite file would vanish after the run and the published record
        # would be overwritten with an empty one - fail loudly instead.
        raise RuntimeError("DATABASE_URL is not set: add it as a repository secret (Settings -> Secrets -> Actions)")
    if not url:
        path = project_root / cfg.get("sqlite_fallback", "data/picks/picks.db")
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"
    # Heroku/Render/Neon style URLs -> SQLAlchemy + psycopg 3 driver
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def connect(url: str) -> Engine:
    # Poolers (Neon "-pooler", PgBouncer) don't reliably support psycopg's automatic
    # server-side prepared statements, so turn them off for Postgres.
    args = {"prepare_threshold": None} if url.startswith("postgresql+psycopg") else {}
    engine = create_engine(url, pool_pre_ping=True, future=True, connect_args=args)
    meta.create_all(engine)
    return engine


def _utc_naive(ts) -> datetime:
    t = pd.Timestamp(ts)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return t.to_pydatetime()


def picks_from_document(doc: dict, markets, tz: str = "Europe/London") -> pd.DataFrame:
    """Best cross-market pick per match in a predictions.json document, ranked within its UK day."""
    rows = []
    for r in doc["predictions"]:
        b = best_pick(r["home"], r["away"], r["probabilities"], r.get("extras") or {}, tuple(markets))
        if b is None:
            continue
        rows.append({
            "match_id": r["id"], "sport": r["sport"], "league": r["league"], "season": r["season"],
            "kickoff": r["kickoff"], "home": r["home"], "away": r["away"], "market": b.market,
            "selection": b.selection, "label": b.label, "probability": round(float(b.p), 4),
            "model": f"{r['model']['name']} v{r['model']['version']}",
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["day"] = pd.to_datetime(df["kickoff"], utc=True).dt.tz_convert(tz).dt.date
    df["day_rank"] = rank_by_day(df, tz)
    return df


def log_picks(engine: Engine, doc: dict, markets, now: datetime) -> tuple[int, int]:
    """Append not-yet-kicked-off picks; skip a match whose latest logged pick is unchanged."""
    df = picks_from_document(doc, markets)
    if df.empty:
        return 0, 0
    now_n = _utc_naive(now)
    df = df[[_utc_naive(k) > now_n for k in df["kickoff"]]]
    with engine.begin() as conn:
        latest = {}
        if len(df):
            sub = (select(picks_log.c.match_id, func.max(picks_log.c.id).label("id"))
                   .where(picks_log.c.match_id.in_(df["match_id"].tolist())).group_by(picks_log.c.match_id).subquery())
            for row in conn.execute(select(picks_log).join(sub, picks_log.c.id == sub.c.id)).mappings():
                latest[row["match_id"]] = row
        new, same = [], 0
        for r in df.to_dict(orient="records"):
            prev = latest.get(r["match_id"])
            rec = {**r, "kickoff": _utc_naive(r["kickoff"]), "logged_at": now_n, "status": doc.get("status", "unknown")}
            if prev is not None and all(prev[k] == rec[k] for k in
                                        ("market", "selection", "probability", "kickoff", "day_rank", "label")):
                same += 1
                continue
            new.append(rec)
        if new:
            conn.execute(picks_log.insert(), new)
    return len(new), same


def settle(engine: Engine, matches: pd.DataFrame, now: datetime, tolerance_days: int = 1,
           void_after_days: int = 3, tz: str = "Europe/London") -> dict[str, int]:
    """Settle every kicked-off match that isn't settled yet, using its latest pre-kickoff pick."""
    now_n = _utc_naive(now)
    counts = {"won": 0, "lost": 0, "void": 0, "pending": 0}
    with engine.begin() as conn:
        done = {r[0] for r in conn.execute(select(official_picks.c.match_id))}
        logs = pd.DataFrame(conn.execute(
            select(picks_log).where(picks_log.c.kickoff <= now_n, picks_log.c.logged_at < picks_log.c.kickoff)
        ).mappings().all())
        if logs.empty:
            return counts
        logs = logs[~logs["match_id"].isin(done)]
        official = logs.sort_values("id").drop_duplicates("match_id", keep="last")
        res = matches[["league", "home", "away", "date", "home_score", "away_score",
                       "odds_home", "odds_draw", "odds_away"]
                      + [c for c in ("odds_over_2_5", "odds_under_2_5") if c in matches]]
        rows = []
        for o in official.to_dict(orient="records"):
            kick_day = pd.Timestamp(o["kickoff"]).tz_localize("UTC").tz_convert(tz).tz_localize(None).normalize()
            cand = res[(res["league"] == o["league"]) & (res["home"] == o["home"]) & (res["away"] == o["away"])
                       & ((res["date"] - kick_day).abs() <= pd.Timedelta(days=tolerance_days))]
            base = {k: o[k] for k in ("match_id", "logged_at", "sport", "league", "season", "kickoff", "home", "away",
                                      "market", "selection", "label", "probability", "day", "day_rank")}
            if len(cand):
                m = cand.iloc[0]
                w = won(o["market"], o["selection"], m["home_score"], m["away_score"])
                rows.append({**base, "state": "won" if w else "lost", "won": w,
                             "home_score": int(m["home_score"]), "away_score": int(m["away_score"]),
                             "closing_odds": closing_odds(o["market"], o["selection"], m),
                             "market_probability": market_probability(o["market"], o["selection"], m),
                             "settled_at": now_n})
                counts["won" if w else "lost"] += 1
            elif now_n - o["kickoff"] > timedelta(days=void_after_days):
                rows.append({**base, "state": "void", "won": None, "home_score": None, "away_score": None,
                             "closing_odds": None, "market_probability": None, "settled_at": now_n})
                counts["void"] += 1
            else:
                counts["pending"] += 1
        if rows:
            conn.execute(official_picks.insert(), rows)
    return counts


def _stats(df: pd.DataFrame) -> dict[str, Any]:
    d = df[df["state"] != "void"]
    out: dict[str, Any] = {"n": int(len(d)), "won": int(d["won"].sum()) if len(d) else 0}
    if len(d):
        out["hit_rate"] = float(d["won"].mean())
        out["avg_probability"] = float(d["probability"].mean())
        mp = d.dropna(subset=["market_probability"])
        if len(mp):
            out["vs_market"] = {"n": int(len(mp)), "ours": float(mp["probability"].mean()),
                                "market": float(mp["market_probability"].mean())}
        priced = d.dropna(subset=["closing_odds"])
        if len(priced):
            profit = np.where(priced["won"].astype(bool), priced["closing_odds"] - 1, -1.0)
            out["priced"] = {"n": int(len(priced)), "profit_units": float(profit.sum()), "roi": float(profit.mean())}
    return out


def summary(engine: Engine, per_day: int, recent: int = 60) -> dict[str, Any]:
    with engine.connect() as conn:
        df = pd.DataFrame(conn.execute(select(official_picks)).mappings().all())
        n_logged = conn.execute(select(func.count()).select_from(picks_log)).scalar_one()
        first = conn.execute(select(func.min(picks_log.c.logged_at))).scalar_one()
    out: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "per_day": per_day, "log_entries": int(n_logged),
        "first_logged": first.isoformat() + "Z" if first else None,
        "settled": int(len(df)),
    }
    if df.empty:
        out.update(top=_stats(pd.DataFrame(columns=["state", "won", "probability"])), recent=[], by_market={}, days=[])
        return out
    top = df[df["day_rank"] <= per_day]
    out["top"] = _stats(top)
    out["all"] = _stats(df)
    out["by_market"] = {k: _stats(g) for k, g in top.groupby("market")}
    days = []
    for day, g in top[top["state"] != "void"].groupby("day"):
        days.append({"day": str(day), "n": int(len(g)), "won": int(g["won"].sum())})
    out["days"] = sorted(days, key=lambda d: d["day"], reverse=True)[:30]
    rec = top.sort_values(["kickoff", "day_rank"], ascending=[False, True]).head(recent)
    out["recent"] = [
        {"match_id": r["match_id"], "league": r["league"], "kickoff": pd.Timestamp(r["kickoff"]).isoformat() + "Z",
         "home": r["home"], "away": r["away"], "label": r["label"], "market": r["market"],
         "probability": float(r["probability"]), "state": r["state"],
         "score": None if r["state"] == "void" else f"{int(r['home_score'])}-{int(r['away_score'])}",
         "logged_at": pd.Timestamp(r["logged_at"]).isoformat() + "Z"}
        for _, r in rec.iterrows()
    ]
    return out
