"""Leakage-free per-match features from results history (form, rest days).

Each value uses only matches strictly before the match it describes.
Rest days only see league matches in the data (no cups/internationals), so they
are an approximation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

POINTS = {"W": 3, "D": 1, "L": 0}


def team_long(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per (match, team) with that team's points and goals."""
    base = matches.reset_index().rename(columns={"index": "match_idx"})
    home = pd.DataFrame({
        "match_idx": base["match_idx"], "date": base["date"], "league": base["league"], "team": base["home"],
        "gf": base["home_score"], "ga": base["away_score"], "side": "home",
    })
    away = pd.DataFrame({
        "match_idx": base["match_idx"], "date": base["date"], "league": base["league"], "team": base["away"],
        "gf": base["away_score"], "ga": base["home_score"], "side": "away",
    })
    long = pd.concat([home, away], ignore_index=True)
    long["pts"] = np.select([long["gf"] > long["ga"], long["gf"] == long["ga"]], [3, 1], 0)
    return long.sort_values(["league", "team", "date", "match_idx"]).reset_index(drop=True)


def form_features(matches: pd.DataFrame, window: int = 5, rest_cap: int = 21) -> pd.DataFrame:
    """Columns per match (indexed like `matches`):
    {home,away}_form_pts, {home,away}_form_gd, {home,away}_rest_days, {home,away}_n_prev.
    """
    long = team_long(matches)
    g = long.groupby(["league", "team"], sort=False)
    prev = lambda s: s.shift(1).rolling(window, min_periods=1).mean()  # noqa: E731
    long["form_pts"] = g["pts"].transform(prev)
    long["form_gd"] = g["gf"].transform(prev) - g["ga"].transform(prev)
    long["rest_days"] = g["date"].diff().dt.days.clip(upper=rest_cap)
    long["n_prev"] = g.cumcount()
    cols = ["form_pts", "form_gd", "rest_days", "n_prev"]
    wide = long.pivot(index="match_idx", columns="side", values=cols)
    wide.columns = [f"{side}_{c}" for c, side in wide.columns]
    return wide.reindex(matches.index)


def involves_promoted_team(matches: pd.DataFrame) -> pd.Series:
    """True for matches involving a team that wasn't in the league the previous
    season (promoted). False throughout each league's first season in the data."""
    teams = {}
    for (lg, season), g in matches.groupby(["league", "season"]):
        teams[(lg, season)] = set(g["home"]) | set(g["away"])
    seasons = {lg: sorted(s for l, s in teams if l == lg) for lg in matches["league"].unique()}
    prev = {(lg, s): (seasons[lg][i - 1] if i else None) for lg in seasons for i, s in enumerate(seasons[lg])}

    def promoted(lg, season, team):
        p = prev[(lg, season)]
        return p is not None and team not in teams[(lg, p)]

    return pd.Series(
        [promoted(l, s, h) or promoted(l, s, a) for l, s, h, a in
         matches[["league", "season", "home", "away"]].itertuples(index=False)],
        index=matches.index,
    )
