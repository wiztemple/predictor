from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from sqlalchemy import select

from predictor.store import connect, database_url, log_picks, official_picks, picks_log, settle, summary

MARKETS = ("1x2", "double_chance", "ou_1_5", "ou_2_5", "ou_3_5", "btts")
T0 = datetime(2026, 10, 7, 6, 0, tzinfo=timezone.utc)


def rec(id_, kickoff, home="Arsenal", away="Leeds", ph=0.6, o15=0.7):
    return {"id": id_, "sport": "football", "league": "E0", "season": "2026-27", "kickoff": kickoff,
            "home": home, "away": away, "model": {"name": "blend", "version": "1.0"},
            "probabilities": {"home": ph, "draw": 0.25, "away": 0.75 - ph},
            "extras": {"over_1_5": o15, "over_2_5": 0.5, "over_3_5": 0.3, "btts": 0.5}}


def doc(*recs):
    return {"status": "preview", "predictions": list(recs)}


@pytest.fixture
def engine(tmp_path):
    return connect(f"sqlite:///{tmp_path / 't.db'}")


def test_database_url_normalises_postgres(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    assert database_url({}, tmp_path) == "postgresql+psycopg://u:p@host:5432/db"
    monkeypatch.delenv("DATABASE_URL")
    assert database_url({"sqlite_fallback": "x/p.db"}, tmp_path).startswith("sqlite:///")


def test_log_only_future_and_skip_unchanged(engine):
    d = doc(rec("a", "2026-10-10T14:00:00Z"), rec("past", "2026-10-06T14:00:00Z"))
    assert log_picks(engine, d, MARKETS, T0) == (1, 0)
    assert log_picks(engine, d, MARKETS, T0 + timedelta(hours=2)) == (0, 1)
    assert log_picks(engine, doc(rec("a", "2026-10-10T14:00:00Z", ph=0.7)), MARKETS, T0 + timedelta(days=1)) == (1, 0)
    with engine.connect() as c:
        rows = c.execute(select(picks_log.c.label, picks_log.c.probability)).all()
    assert rows[0] == ("Arsenal or draw", 0.85) and rows[1] == ("Arsenal or draw", 0.95)


def test_settle_uses_latest_pre_kickoff_pick_and_handles_void(engine):
    log_picks(engine, doc(rec("a", "2026-10-10T14:00:00Z", ph=0.3, o15=0.9),
                          rec("p", "2026-10-10T16:00:00Z", home="Chelsea", away="Everton")), MARKETS, T0)
    log_picks(engine, doc(rec("a", "2026-10-10T14:00:00Z", ph=0.7)), MARKETS, T0 + timedelta(days=2))
    results = pd.DataFrame({
        "league": ["E0"], "home": ["Arsenal"], "away": ["Leeds"], "date": pd.to_datetime(["2026-10-10"]),
        "home_score": [0], "away_score": [1], "odds_home": [1.6], "odds_draw": [4.0], "odds_away": [6.0],
        "odds_over_2_5": [1.8], "odds_under_2_5": [2.0],
    })
    counts = settle(engine, results, datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert counts == {"won": 0, "lost": 1, "void": 1, "pending": 0}
    with engine.connect() as c:
        rows = {r["match_id"]: r for r in c.execute(select(official_picks)).mappings()}
    a = rows["a"]
    assert a["label"] == "Arsenal or draw" and a["probability"] == 0.95  # the later pre-kickoff pick counts
    assert a["state"] == "lost" and a["market_probability"] == pytest.approx(0.6 + 0.24, abs=0.03)
    assert rows["p"]["state"] == "void"
    # settling again does nothing (append-only, idempotent)
    assert settle(engine, results, datetime(2026, 10, 16, tzinfo=timezone.utc)) == {"won": 0, "lost": 0, "void": 0, "pending": 0}

    s = summary(engine, per_day=10)
    assert s["settled"] == 2 and s["top"]["n"] == 1 and s["top"]["won"] == 0
    assert s["recent"][0]["state"] in ("lost", "void")


def test_migrate_copies_once(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    src_path = tmp_path / "local.db"
    src = connect(f"sqlite:///{src_path}")
    log_picks(src, doc(rec("a", "2026-10-10T14:00:00Z")), MARKETS, T0)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'target.db'}")
    spec = importlib.util.spec_from_file_location("mig", Path(__file__).parents[1] / "scripts" / "migrate_picks.py")
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    monkeypatch.setattr(mig, "load_config", lambda: {"picks": {"sqlite_fallback": str(src_path)}})
    monkeypatch.setattr(mig, "project_path", lambda p: Path(p))
    assert mig.main() == 0 and mig.main() == 0  # second run copies nothing
    with connect(f"sqlite:///{tmp_path / 'target.db'}").connect() as c:
        assert len(c.execute(select(picks_log)).all()) == 1


def test_ci_without_database_url_fails_loudly(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        database_url({}, tmp_path)


LISTS = {"safe": {"label": "Safe 10", "kind": "any"},
         "bold": {"label": "Bold 10", "kind": "band", "min_odds": 1.6, "max_odds": 2.0},
         "wins": {"label": "Winners 10", "kind": "wins"}}


def test_weekly_lists_lock_once_and_settle(engine):
    from predictor.store import lock_weekly, settle_weekly, week_bounds, weekly_summary

    assert [str(d) for d in week_bounds(pd.Timestamp("2026-10-08T10:00Z"))] == ["2026-10-06", "2026-10-12"]
    now = datetime(2026, 10, 8, 6, tzinfo=timezone.utc)
    d = doc(*[rec(f"m{i}", f"2026-10-{10 + i % 3}T14:00:00Z", home=f"H{i}", away=f"A{i}", ph=0.3 + i * 0.04)
              for i in range(12)],
            rec("past", "2026-10-07T14:00:00Z", home="Old", away="Game", ph=0.9),
            rec("next", "2026-10-14T14:00:00Z", home="Next", away="Week", ph=0.95))
    locked = lock_weekly(engine, d, LISTS, now, markets=MARKETS)
    assert locked["safe"] == 10 and locked["wins"] == 10 and 0 < locked.get("bold", 0) <= 10
    assert lock_weekly(engine, d, LISTS, now + timedelta(days=1), markets=MARKETS) == {}  # already locked
    s = weekly_summary(engine, LISTS)
    safe, wins = s["lists"]["safe"]["weeks"][0], s["lists"]["wins"]["weeks"][0]
    assert len(safe["picks"]) == 10 and safe["pending"] == 10
    assert {p["home"] for p in safe["picks"]}.isdisjoint({"Old", "Next"})
    assert all(p["market"] == "1x2" for p in wins["picks"])
    assert all(0.5 <= p["probability"] <= 0.625 for p in s["lists"]["bold"]["weeks"][0]["picks"])
    top = wins["picks"][0]
    results = pd.DataFrame({"league": ["E0"], "home": [top["home"]], "away": [top["away"]],
                            "date": [pd.Timestamp(top["kickoff"][:10])], "home_score": [2], "away_score": [0]})
    settle_weekly(engine, results, datetime(2026, 10, 16, tzinfo=timezone.utc))
    w = weekly_summary(engine, LISTS)["lists"]["wins"]["weeks"][0]
    assert w["picks"][0]["state"] == "won" and w["picks"][0]["score"] == "2-0" and w["pending"] == 0


def test_weekly_v1_rows_migrate_as_safe(engine):
    from predictor.store import migrate_weekly_v1, weekly_picks, weekly_summary

    with engine.begin() as c:
        c.execute(weekly_picks.insert(), [{"week_start": pd.Timestamp("2026-10-06").date(), "rank": 1,
                                           "week_end": pd.Timestamp("2026-10-12").date(), "locked_at": datetime(2026, 10, 8),
                                           "match_id": "x", "league": "E0", "kickoff": datetime(2026, 10, 10, 14),
                                           "home": "A", "away": "B", "market": "double_chance", "selection": "1x",
                                           "label": "A or draw", "probability": 0.9}])
    assert migrate_weekly_v1(engine) == 1 and migrate_weekly_v1(engine) == 0
    assert weekly_summary(engine, LISTS)["lists"]["safe"]["weeks"][0]["picks"][0]["label"] == "A or draw"


def test_export_audit_writes_every_row(engine, tmp_path):
    import json

    from predictor.store import export_audit

    log_picks(engine, doc(rec("a", "2026-10-10T14:00:00Z"), rec("b", "2026-10-11T14:00:00Z", home="X", away="Y")),
              MARKETS, T0)
    counts = export_audit(engine, tmp_path)
    assert counts["picks_log"] == 2
    rows = [json.loads(l) for l in open(tmp_path / "picks_log.jsonl")]
    assert [r["match_id"] for r in rows] == ["a", "b"] and all(r["logged_at"] < r["kickoff"] for r in rows)
