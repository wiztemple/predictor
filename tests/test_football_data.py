import numpy as np
import pandas as pd
import pytest

from predictor.config import season_codes, season_label
from predictor.loaders.football_data import (
    clean_file,
    load_matches,
    parse_dates,
    read_raw_csv,
    select_odds,
)

PRIORITY = [
    ["pinnacle_closing", "PSCH", "PSCD", "PSCA"],
    ["avg_closing", "AvgCH", "AvgCD", "AvgCA"],
    ["pinnacle_opening", "PSH", "PSD", "PSA"],
]

CSV = (
    "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,PSH,PSD,PSA,PSCH,PSCD,PSCA,AvgCH,AvgCD,AvgCA\n"
    "E0,09/08/19,Liverpool,Norwich,4,1,H,1.20,7.0,15.0,1.18,7.5,17.0,1.17,7.2,16.0\n"
    "E0,10/08/2019,West Ham,Man City,0,5,A,10.0,6.0,1.30,,,,11.0,6.5,1.28\n"
    "E0,10/08/2019,Burnley,Southampton,3,0,H,2.5,3.2,3.0,,,,,,,extra,fields\n"
    ",,,,,,,,,,,,,,,\n"
)


def test_season_helpers():
    assert season_codes("1920", "2223") == ["1920", "2021", "2122", "2223"]
    assert season_codes("2526", "2627") == ["2526", "2627"]
    assert season_label("2526") == "2025-26"


def test_parse_dates_mixed_formats():
    s = pd.Series(["09/08/19", "10/08/2019", "", None, "31/12/99"])
    out = parse_dates(s)
    assert out[0] == pd.Timestamp("2019-08-09")
    assert out[1] == pd.Timestamp("2019-08-10")
    assert pd.isna(out[2]) and pd.isna(out[3])
    assert out[4] == pd.Timestamp("1999-12-31")


def test_select_odds_priority_and_fallback():
    raw = pd.DataFrame(
        {
            "PSCH": ["1.5", "", "1.0"], "PSCD": ["4", "", "3"], "PSCA": ["6", "", "5"],
            "AvgCH": ["1.4", "2.0", ""], "AvgCD": ["4", "3.3", ""], "AvgCA": ["6", "3.8", ""],
            "PSH": ["1.6", "2.1", "2.2"], "PSD": ["4", "3", "3.1"], "PSA": ["5", "3.5", "3.4"],
        }
    )
    out = select_odds(raw, PRIORITY)
    assert list(out["odds_source"]) == ["pinnacle_closing", "avg_closing", "pinnacle_opening"]
    assert out.loc[0, "odds_home"] == 1.5
    assert out.loc[1, "odds_away"] == 3.8
    # 1.0 is not a valid decimal price, so row 2 falls through to opening odds
    assert out.loc[2, "odds_home"] == 2.2


def test_select_odds_missing_columns():
    out = select_odds(pd.DataFrame({"X": ["1"]}), PRIORITY)
    assert out["odds_source"].isna().all() and np.isnan(out["odds_home"]).all()


def test_read_and_clean(tmp_path):
    p = tmp_path / "E0_1920.csv"
    p.write_bytes(CSV.encode("latin-1"))
    raw = read_raw_csv(p)
    assert "Div" in raw.columns and len(raw) == 4
    df = clean_file(raw, "E0", "1920", PRIORITY)
    assert len(df) == 3  # blank row dropped, ragged row kept
    assert list(df["outcome"]) == ["H", "A", "H"]
    assert list(df["odds_source"]) == ["pinnacle_closing", "avg_closing", "pinnacle_opening"]
    assert (df["season"] == "2019-20").all() and (df["sport"] == "football").all()


def test_latin1_and_bom(tmp_path):
    p = tmp_path / "SP1_2021.csv"
    content = "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG\nSP1,12/09/20,Alavés,Betis,0,1\n"
    p.write_bytes(content.encode("latin-1"))
    raw = read_raw_csv(p)
    assert raw.loc[0, "HomeTeam"] == "Alavés"
    p.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    assert read_raw_csv(p).columns[0] == "Div"


def test_load_matches_dedup(tmp_path):
    (tmp_path / "E0_1920.csv").write_text(CSV)
    (tmp_path / "E0_1920_copy.csv").write_text(CSV)  # ignored: name doesn't match pattern
    (tmp_path / "D1_1920.csv").write_text(CSV.replace("E0,", "D1,"))
    df = load_matches(tmp_path, leagues=["E0", "D1"])
    assert len(df) == 6
    assert df["date"].is_monotonic_increasing
    with pytest.raises(Exception):
        # the shared validator rejects duplicates
        from predictor.schema import validate_matches
        validate_matches(pd.concat([df, df]))


def test_select_ou_odds_priority():
    from predictor.loaders.football_data import select_ou_odds

    raw = pd.DataFrame({"PC>2.5": ["1.9", ""], "PC<2.5": ["2.0", ""], "AvgC>2.5": ["1.85", "2.2"],
                        "AvgC<2.5": ["1.95", "1.7"]})
    pr = [["pinnacle_closing", "PC>2.5", "PC<2.5"], ["avg_closing", "AvgC>2.5", "AvgC<2.5"]]
    out = select_ou_odds(raw, pr)
    assert list(out["ou_source"]) == ["pinnacle_closing", "avg_closing"]
    assert out.loc[1, "odds_under_2_5"] == 1.7


def test_drop_excluded_forfeits():
    from predictor.loaders.football_data import drop_excluded

    df = pd.DataFrame({"league": ["T1"] * 3, "season": ["2022-23"] * 3,
                       "date": pd.to_datetime(["2023-01-10", "2023-03-05", "2023-03-05"]),
                       "home": ["Hatayspor", "Hatayspor", "Konyaspor"], "away": ["X", "Y", "Z"]})
    out = drop_excluded(df, [{"league": "T1", "season": "2022-23", "teams": ["Hatayspor"], "from": "2023-02-06"}])
    assert list(out.index) == [0, 2]  # before withdrawal kept, unrelated match kept


def test_extra_league_loader(tmp_path):
    from predictor.loaders.football_data_extra import clean_extra, season_from_extra

    csv = ("Country,League,Season,Date,Time,Home,Away,HG,AG,Res,PSCH,PSCD,PSCA,AvgCH,AvgCD,AvgCA\n"
           "Switzerland,Super League,2018/2019,20/07/2018,18:00,Basel,Sion,2,1,H,1.5,4,6,1.5,4,6\n"
           "Switzerland,Super League,2019/2020,20/07/2019,18:00,Basel,Sion,0,0,D,,,,1.6,3.9,5.5\n"
           "Switzerland,Challenge League,2019/2020,21/07/2019,18:00,Aarau,Thun,1,2,A,2,3,3,2,3,3\n"
           "Denmark ,Superliga ,2019/2020,22/07/2019,18:00,Brondby ,FC Copenhagen,1,3,A,3,3.4,2.2,3,3.4,2.2\n")
    p = tmp_path / "x.csv"
    p.write_text(csv)
    raw = read_raw_csv(p)
    pr = [["pinnacle_closing", "PSCH", "PSCD", "PSCA"], ["avg_closing", "AvgCH", "AvgCD", "AvgCA"]]
    swz = clean_extra(raw, "SWZ", "Switzerland", "Super League", pr, "2019-20")
    assert len(swz) == 1  # 2018-19 dropped, Challenge League excluded
    assert swz["season"].iat[0] == "2019-20" and swz["outcome"].iat[0] == "D"
    assert swz["odds_source"].iat[0] == "avg_closing"
    dnk = clean_extra(raw, "DNK", "Denmark", "Superliga", pr, "2019-20")
    assert dnk["home"].iat[0] == "Brondby"  # whitespace stripped
    with pytest.raises(ValueError):
        season_from_extra(pd.Series(["2020"]))


def test_apply_renames_is_per_league():
    from predictor.loaders.football_data import apply_renames

    df = pd.DataFrame({"league": ["POL", "XX"], "home": ["Gornik Z.", "Gornik Z."], "away": ["Legia", "Gornik Z."]})
    out = apply_renames(df, {"POL": {"Gornik Z.": "Gornik Zabrze"}})
    assert list(out["home"]) == ["Gornik Zabrze", "Gornik Z."]
    assert out.loc[1, "away"] == "Gornik Z."
