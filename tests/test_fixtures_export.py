import numpy as np
import json

import pandas as pd
import pytest

from predictor.export import build_document
from predictor.fixtures import combine, parse_football_data_fixtures, parse_fixturedownload
from predictor.models import DixonColesModel, EloModel
from predictor.teams import TeamNameMapper


@pytest.fixture
def mapper():
    hist = pd.DataFrame({"league": ["E0", "E0", "SP1"], "home": ["Man United", "Tottenham", "Ath Madrid"],
                         "away": ["Arsenal", "Arsenal", "Betis"]})
    m = TeamNameMapper.from_history(hist, "/nonexistent")
    m.aliases = {"Man Utd": "Man United", "Spurs": "Tottenham", "Atlético de Madrid": "Ath Madrid",
                 "Typo FC": "Nonexistent"}
    return m


def test_mapper_exact_alias_and_unknown(mapper):
    assert mapper.match("E0", "Arsenal") == "Arsenal"
    assert mapper.match("E0", "Man Utd") == "Man United"
    assert mapper.match("SP1", "Atlético de Madrid") == "Ath Madrid"
    # alias must point at a team in THAT league
    assert mapper.match("SP1", "Spurs") is None
    # no fuzzy matching at runtime
    assert mapper.match("E0", "Manchester Utd") is None
    assert "Man United" in mapper.suggest("E0", "Manchester Utd")
    assert mapper.unknown_aliases() == {"Typo FC": "Nonexistent"}


def test_parse_football_data_fixtures_timezone():
    csv = "﻿Div,Date,Time,HomeTeam,AwayTeam\nE0,10/10/2026,15:00,Arsenal,Spurs\nE2,10/10/2026,15:00,X,Y\n"
    df = parse_football_data_fixtures(csv.encode("utf-8"), ["E0"], "Europe/London")
    assert len(df) == 1
    assert df["kickoff"].iat[0] == pd.Timestamp("2026-10-10 14:00", tz="UTC")  # BST = UTC+1
    assert parse_football_data_fixtures(b"", ["E0"], "Europe/London").empty


def test_parse_fixturedownload_keeps_unplayed_only():
    recs = [
        {"DateUtc": "2026-10-10 14:00:00Z", "HomeTeam": "Arsenal", "AwayTeam": "Spurs", "HomeTeamScore": None},
        {"DateUtc": "2026-09-10 14:00:00Z", "HomeTeam": "Spurs", "AwayTeam": "Arsenal", "HomeTeamScore": 1},
    ]
    df = parse_fixturedownload(recs, "E0")
    assert list(df["home"]) == ["Arsenal"] and str(df["kickoff"].dt.tz) == "UTC"


def test_combine_prefers_earlier_source_and_handles_reschedule(mapper):
    a = pd.DataFrame({"league": ["E0"], "kickoff": [pd.Timestamp("2026-10-10 14:00", tz="UTC")],
                      "home": ["Arsenal"], "away": ["Spurs"], "source": ["football-data"]})
    b = pd.DataFrame({"league": ["E0", "E0"], "kickoff": pd.to_datetime(["2026-10-11 15:00", "2026-10-11 15:00"], utc=True),
                      "home": ["Arsenal", "Mystery FC"], "away": ["Tottenham", "Arsenal"], "source": ["fixturedownload"] * 2})
    for f in (a, b):
        f["home_mapped"] = [mapper.match(l, n) for l, n in zip(f["league"], f["home"])]
        f["away_mapped"] = [mapper.match(l, n) for l, n in zip(f["league"], f["away"])]
    out = combine([a, b])
    assert len(out) == 2  # Arsenal-Spurs once (football-data wins), unmatched Mystery FC kept, not dropped
    assert out.loc[out["home"] == "Arsenal", "source"].iat[0] == "football-data"
    assert out["home_mapped"].isna().sum() == 1


def test_build_document_schema(sim):
    df, truth = sim
    dc, elo = DixonColesModel().fit(df), EloModel().fit(df)
    fx = pd.DataFrame({"league": ["XX", "XX"], "kickoff": pd.to_datetime(["2023-01-07 15:00", "2023-01-08 00:00"], utc=True),
                       "home": ["a", "b"], "away": ["c", "d"],
                       "home_mapped": [truth["teams"][0], truth["teams"][2]], "away_mapped": [truth["teams"][1], truth["teams"][3]],
                       "source": ["test", "test"], "season": ["2022-23"] * 2})
    doc = build_document(fx, dc, [elo], [], {"XX": "Test League"}, df["date"].max(), "preview", 6)
    json.dumps(doc)  # serialisable
    assert doc["status"] == "preview" and len(doc["predictions"]) == 2
    rec = doc["predictions"][0]
    for k in ("sport", "league", "kickoff", "home", "away", "probabilities", "extras", "model", "generated_at"):
        assert k in rec
    assert sum(rec["probabilities"].values()) == pytest.approx(1, abs=1e-3)
    grid = rec["extras"]["score_grid"]
    assert len(grid["cells"]) == 7 and sum(map(sum, grid["cells"])) + grid["other"] == pytest.approx(1, abs=1e-3)
    assert rec["other_models"][0]["name"] == "elo"
    assert rec["kickoff_tbc"] is False and doc["predictions"][1]["kickoff_tbc"] is True
    assert rec["home"] == truth["teams"][0]


def test_fixturedownload_falls_back_to_cache(tmp_path, monkeypatch):
    import predictor.fixtures as fx

    good = [{"DateUtc": "2026-10-10 14:00:00Z", "HomeTeam": "A", "AwayTeam": "B", "HomeTeamScore": None}]
    calls = {"n": 0}

    class Resp:
        def json(self):
            return good

    def ok(url, ua, timeout=30):
        return Resp()

    def fail(url, ua, timeout=30):
        calls["n"] += 1
        raise ConnectionError("reset")

    monkeypatch.setattr(fx, "_get", ok)
    first = fx.fetch_fixturedownload("u/{slug}-{year}", {"E0": "epl"}, 2026, "ua", cache_dir=tmp_path, backoff=0)
    monkeypatch.setattr(fx, "_get", fail)
    second = fx.fetch_fixturedownload("u/{slug}-{year}", {"E0": "epl"}, 2026, "ua", cache_dir=tmp_path,
                                      retries=2, backoff=0)
    assert calls["n"] == 3  # 1 try + 2 retries
    assert len(first) == len(second) == 1
    empty = fx.fetch_fixturedownload("u/{slug}-{year}", {"E0": "epl"}, 2026, "ua", cache_dir=tmp_path / "none",
                                     retries=0, backoff=0)
    assert empty.empty


def test_build_document_applies_goals_calibration(sim):
    df, truth = sim
    dc = DixonColesModel().fit(df)
    fx = pd.DataFrame({"league": ["XX"], "kickoff": pd.to_datetime(["2023-01-07 15:00"], utc=True),
                       "home": ["a"], "away": ["b"], "home_mapped": [truth["teams"][0]],
                       "away_mapped": [truth["teams"][1]], "source": ["t"], "season": ["2022-23"]})
    raw = build_document(fx, dc, [], [], {"XX": "X"}, df["date"].max(), "preview", 6)
    shrink = {"markets": {k: {"method": "platt", "a": 0.5, "b": 0.0} for k in ("over_1_5", "over_2_5", "over_3_5", "btts")}}
    cal = build_document(fx, dc, [], [], {"XX": "X"}, df["date"].max(), "preview", 6, goals_calibration=shrink)
    r, c = raw["predictions"][0]["extras"], cal["predictions"][0]["extras"]
    assert abs(c["over_2_5"] - 0.5) < abs(r["over_2_5"] - 0.5)  # pulled toward 50%
    assert c["goals_calibrated"] and not r["goals_calibrated"]
    assert c["score_grid"] == r["score_grid"]  # grid stays raw
    assert raw["predictions"][0]["probabilities"] == cal["predictions"][0]["probabilities"]


def test_parse_extra_fixtures_maps_country_and_league():
    from predictor.fixtures import parse_extra_fixtures

    csv = ("﻿Country,League,Date,Time,Home,Away\n"
           "Romania,Superliga,10/10/2026,18:30,FCSB,CFR Cluj\n"
           "Denmark ,Superliga ,11/10/2026,14:00,Brondby,Aarhus\n"
           "Argentina,Liga Profesional,10/10/2026,23:15,Boca,River\n")
    extra = {"ROU": {"country": "Romania", "league": "Superliga"}, "DNK": {"country": "Denmark", "league": "Superliga"}}
    df = parse_extra_fixtures(csv.encode("utf-8"), extra, "Europe/London")
    assert list(df["league"]) == ["ROU", "DNK"]  # same league name, told apart by country; Argentina ignored
    assert df["kickoff"].iat[0] == pd.Timestamp("2026-10-10 17:30", tz="UTC")


def test_build_document_exports_margins_consistent_with_1x2(sim):
    from predictor.handicap import home_outcome
    from predictor.models import BlendModel

    df, truth = sim
    m = BlendModel().fit(df)
    fx = pd.DataFrame({"league": ["XX"], "kickoff": pd.to_datetime(["2023-01-07 15:00"], utc=True),
                       "home": ["a"], "away": ["b"], "home_mapped": [truth["teams"][0]],
                       "away_mapped": [truth["teams"][3]], "source": ["t"], "season": ["2022-23"]})
    rec = build_document(fx, m, [], [], {"XX": "X"}, df["date"].max(), "preview", 6)["predictions"][0]
    mg = np.array(rec["extras"]["margin"]["probs"])
    assert len(mg) == 2 * rec["extras"]["margin"]["cap"] + 1 and mg.sum() == pytest.approx(1, abs=1e-3)
    assert home_outcome(mg, -0.5)[0] == pytest.approx(rec["probabilities"]["home"], abs=1e-3)


def test_build_document_ten_minute_result(sim):
    df, truth = sim
    dc = DixonColesModel().fit(df)
    fx = pd.DataFrame({"league": ["XX"], "kickoff": pd.to_datetime(["2023-01-07 15:00"], utc=True),
                       "home": ["a"], "away": ["b"], "home_mapped": [truth["teams"][0]],
                       "away_mapped": [truth["teams"][1]], "source": ["t"], "season": ["2022-23"]})
    rec = build_document(fx, dc, [], [], {"XX": "X"}, df["date"].max(), "preview", 6,
                         ten_min_share=0.085)["predictions"][0]
    t = rec["extras"]["ten_min"]
    assert t["home"] + t["draw"] + t["away"] == pytest.approx(1, abs=2e-4)
    assert 0.6 < t["no_goal"] <= t["draw"] < 0.95


def test_build_document_extra_markets_consistent(sim):
    from predictor.models import BlendModel

    df, truth = sim
    m = BlendModel().fit(df)
    fx = pd.DataFrame({"league": ["XX"], "kickoff": pd.to_datetime(["2023-01-07 15:00"], utc=True),
                       "home": ["a"], "away": ["b"], "home_mapped": [truth["teams"][0]],
                       "away_mapped": [truth["teams"][3]], "source": ["t"], "season": ["2022-23"]})
    rec = build_document(fx, m, [], [], {"XX": "X"}, df["date"].max(), "preview", 6,
                         half_share=0.445)["predictions"][0]
    mk, pr, x = rec["extras"]["markets"], rec["probabilities"], rec["extras"]
    assert mk["result_btts"]["1&GG"] + mk["result_btts"]["1&NG"] == pytest.approx(pr["home"], abs=2e-4)
    assert sum(v for k, v in mk["result_ou25"].items() if k.endswith("&O")) == pytest.approx(x["over_2_5"], abs=3e-4)
    assert sum(v for k, v in mk["htft"].items() if k.endswith("/X")) == pytest.approx(pr["draw"], abs=3e-4)
    assert x["grid_adjusted"] and sum(map(sum, x["score_grid"]["cells"])) + x["score_grid"]["other"] == pytest.approx(1, abs=2e-3)
