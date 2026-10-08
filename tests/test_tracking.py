from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from predictor.tracking import attach_results, live_summary, load_log, log_predictions, official_predictions

T0 = datetime(2026, 10, 7, 6, 0, tzinfo=timezone.utc)


def rec(id_, kickoff, home="Arsenal", away="Leeds", p=(0.6, 0.25, 0.15), league="E0"):
    return {
        "id": id_, "sport": "football", "league": league, "season": "2026-27", "kickoff": kickoff,
        "home": home, "away": away, "model": {"name": "blend", "version": "1.0"},
        "probabilities": {"home": p[0], "draw": p[1], "away": p[2]},
        "extras": {"over_2_5": 0.5, "btts": 0.5}, "other_models": [],
    }


def doc(*recs):
    return {"status": "preview", "predictions": list(recs)}


def test_log_only_future_and_skips_unchanged(tmp_path):
    d = doc(rec("a", "2026-10-10T14:00:00Z"), rec("past", "2026-10-06T14:00:00Z"))
    assert log_predictions(d, tmp_path, T0) == (1, 0)          # past kickoff never logged
    assert log_predictions(d, tmp_path, T0 + timedelta(hours=1)) == (0, 1)  # unchanged -> skipped
    d2 = doc(rec("a", "2026-10-10T14:00:00Z", p=(0.55, 0.27, 0.18)))
    assert log_predictions(d2, tmp_path, T0 + timedelta(days=1)) == (1, 0)  # changed -> new entry
    entries = load_log(tmp_path)
    assert [e["id"] for e in entries] == ["a", "a"]
    assert entries[0]["logged_at"] == "2026-10-07T06:00:00Z"


def test_log_is_append_only_across_months(tmp_path):
    log_predictions(doc(rec("a", "2026-11-02T14:00:00Z")), tmp_path, T0)
    log_predictions(doc(rec("a", "2026-11-02T14:00:00Z", p=(0.5, 0.3, 0.2))), tmp_path, datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert sorted(f.name for f in tmp_path.iterdir()) == ["2026-10.jsonl", "2026-11.jsonl"]


def _results(*rows):
    return pd.DataFrame(rows, columns=["league", "home", "away", "date", "home_score", "away_score", "outcome",
                                       "odds_home", "odds_draw", "odds_away"]).assign(date=lambda d: pd.to_datetime(d["date"]))


def test_official_is_latest_before_kickoff(tmp_path):
    log_predictions(doc(rec("a", "2026-10-10T14:00:00Z", p=(0.6, 0.25, 0.15))), tmp_path, T0)
    log_predictions(doc(rec("a", "2026-10-10T14:00:00Z", p=(0.5, 0.3, 0.2))), tmp_path, T0 + timedelta(days=2))
    # an entry written after kickoff (e.g. hand-edited) must never count
    with open(tmp_path / "2026-10.jsonl", "a") as fh:
        import json
        e = load_log(tmp_path)[-1] | {"logged_at": "2026-10-10T15:00:00Z", "probabilities": {"home": 1.0, "draw": 0.0, "away": 0.0}}
        fh.write(json.dumps(e) + "\n")
    off = official_predictions(load_log(tmp_path))
    assert len(off) == 1 and off["p_home"].iat[0] == 0.5


def test_attach_results_states_and_bookmaker(tmp_path):
    log_predictions(doc(
        rec("played", "2026-10-10T14:00:00Z"),
        rec("postponed", "2026-10-10T16:30:00Z", home="Chelsea", away="Everton"),
        rec("later", "2026-10-18T14:00:00Z", home="Fulham", away="Hull"),
    ), tmp_path, T0)
    results = _results(
        ("E0", "Arsenal", "Leeds", "2026-10-10", 2, 0, "H", 1.5, 4.0, 7.0),
        ("E0", "Arsenal", "Leeds", "2025-12-01", 1, 1, "D", 1.5, 4.0, 7.0),   # old meeting, ignored
        ("E0", "Chelsea", "Everton", "2026-11-20", 0, 1, "A", 2.0, 3.4, 4.0),  # rearranged much later
    )
    now = datetime(2026, 10, 15, tzinfo=timezone.utc)
    m = attach_results(official_predictions(load_log(tmp_path)), results, now).set_index("id")
    assert m.loc["played", "state"] == "scored" and m.loc["played", "outcome"] == "H"
    assert m.loc["played", "home_score"] == 2
    assert m.loc["postponed", "state"] == "void"
    assert m.loc["later", "state"] == "pending"
    assert m.loc["played", ["bk_p_home", "bk_p_draw", "bk_p_away"]].sum() == pytest.approx(1)

    s = live_summary(m.reset_index(), "blend")
    assert (s["n_scored"], s["n_pending"], s["n_void"]) == (1, 1, 1)
    assert s["same_matches_with_odds"]["n"] == 1
    assert s["recent"][0]["id"] == "later"


def test_empty_log_summary():
    assert live_summary(official_predictions([]), "blend")["n_scored"] == 0
