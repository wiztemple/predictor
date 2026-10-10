import json

import pandas as pd

from predictor.loaders.espn_results import fetch_espn_results, load_espn_results, parse_results
from predictor.teams import TeamNameMapper

COLS = ["sport", "league", "season", "date", "home", "away", "home_score", "away_score", "outcome",
        "odds_home", "odds_draw", "odds_away", "odds_source", "home_corners", "away_corners", "results_source"]


def _event(date, home, away, hs, as_, status="STATUS_FULL_TIME", completed=True, hc="5", ac="3"):
    def side(where, name, score, corners):
        return {"homeAway": where, "team": {"displayName": name}, "score": str(score),
                "statistics": [{"name": "wonCorners", "displayValue": corners}]}
    return {"date": date, "competitions": [{
        "status": {"type": {"name": status, "completed": completed}},
        "competitors": [side("home", home, hs, hc), side("away", away, as_, ac)]}]}


def test_parse_keeps_finished_only():
    p = {"events": [
        _event("2026-10-09T19:00Z", "West Ham United", "Queens Park Rangers", 1, 1),
        _event("2026-10-10T14:00Z", "Hull City", "Leeds United", 0, 0, "STATUS_SCHEDULED", False),
        _event("2026-10-09T19:00Z", "A", "B", 0, 0, "STATUS_POSTPONED", True),
    ]}
    r = parse_results(p, "E1")
    assert len(r) == 1
    assert (r.loc[0, "home_score"], r.loc[0, "away_score"], r.loc[0, "home_corners"]) == (1, 1, 5.0)


def _setup(tmp_path):
    hist = pd.DataFrame({"league": ["E1", "E1"], "home": ["West Ham", "Hull"], "away": ["QPR", "Leeds"]})
    alias = tmp_path / "names.yaml"
    alias.write_text("football:\n  West Ham United: West Ham\n")
    d = tmp_path / "cache" / "eng.2"
    d.mkdir(parents=True)
    (d / "20261009.json").write_text(json.dumps({"events": [
        _event("2026-10-09T19:00Z", "West Ham United", "QPR", 2, 1),
        _event("2026-10-09T19:00Z", "Mystery FC", "Hull", 0, 0),
    ]}))
    (d / "20260920.json").write_text(json.dumps({"events": [_event("2026-09-20T14:00Z", "Hull", "Leeds", 1, 0)]}))
    return TeamNameMapper.from_history(hist, alias), tmp_path / "cache"


def test_load_maps_names_reports_unknown_and_respects_cutoff(tmp_path):
    mapper, cache = _setup(tmp_path)
    df, unmatched = load_espn_results(cache, {"E1": "eng.2"}, mapper, {"E1": pd.Timestamp("2026-09-20")}, COLS)
    assert list(df.columns) == COLS
    assert len(df) == 1  # the 20 Sep match is already covered by football-data; Mystery FC unmapped
    r = df.iloc[0]
    assert (r["home"], r["away"], r["outcome"], r["results_source"]) == ("West Ham", "QPR", "H", "espn")
    assert r["season"] == "2026-27" and r["date"] == pd.Timestamp("2026-10-09")
    assert [u["name"] for u in unmatched] == ["Mystery FC"]


def test_fetch_skips_cached_old_days(tmp_path):
    calls = []
    def get(url):
        calls.append(url)
        return {"events": []}
    since = {"E1": pd.Timestamp("2026-10-01")}
    n, bad = fetch_espn_results("u/{slug}/{date}", {"E1": "eng.2"}, since, pd.Timestamp("2026-10-05"),
                                tmp_path, get, delay=0)
    assert n == 4 and not bad  # 2..5 Oct
    calls.clear()
    fetch_espn_results("u/{slug}/{date}", {"E1": "eng.2"}, since, pd.Timestamp("2026-10-05"), tmp_path, get, delay=0)
    assert calls == ["u/eng.2/20261003", "u/eng.2/20261004", "u/eng.2/20261005"]  # only the recent days again
