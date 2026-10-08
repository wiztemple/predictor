"""Cross-market picks: the single most likely selection per match, and settlement.

The same functions are used live (predict_fixtures), for storage/settlement, and
in the backtest, so the rule being tracked is exactly the rule shown on the site.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# market -> selections; a selection's probability comes from match probabilities
MARKETS = ("1x2", "double_chance", "ou_1_5", "ou_2_5", "ou_3_5", "btts")


@dataclass(frozen=True)
class Selection:
    market: str
    selection: str
    label: str
    p: float


def candidates(home: str, away: str, probs: dict, extras: dict, markets=MARKETS) -> list[Selection]:
    """All selections for one match. `probs` has home/draw/away; `extras` has over_1_5/over_2_5/over_3_5/btts."""
    h, d, a = probs["home"], probs["draw"], probs["away"]
    out: list[Selection] = []
    if "1x2" in markets:
        out += [Selection("1x2", "home", f"{home} win", h), Selection("1x2", "draw", "Draw", d),
                Selection("1x2", "away", f"{away} win", a)]
    if "double_chance" in markets:
        out += [Selection("double_chance", "1x", f"{home} or draw", h + d),
                Selection("double_chance", "12", f"{home} or {away}", h + a),
                Selection("double_chance", "x2", f"{away} or draw", d + a)]
    for line in ("1_5", "2_5", "3_5"):
        key, mk = f"over_{line}", f"ou_{line}"
        if mk in markets and extras.get(key) is not None:
            pretty = line.replace("_", ".")
            out += [Selection(mk, "over", f"Over {pretty}", extras[key]),
                    Selection(mk, "under", f"Under {pretty}", 1 - extras[key])]
    if "btts" in markets and extras.get("btts") is not None:
        out += [Selection("btts", "yes", "Both teams score", extras["btts"]),
                Selection("btts", "no", "Not both score", 1 - extras["btts"])]
    return out


def best_pick(home: str, away: str, probs: dict, extras: dict, markets=MARKETS) -> Selection | None:
    """Most likely selection; ties broken by market order (stable)."""
    cs = candidates(home, away, probs, extras, markets)
    return max(cs, key=lambda s: s.p) if cs else None


def won(market: str, selection: str, home_score: int, away_score: int) -> bool:
    hs, as_ = int(home_score), int(away_score)
    total = hs + as_
    if market == "1x2":
        return {"home": hs > as_, "draw": hs == as_, "away": hs < as_}[selection]
    if market == "double_chance":
        return {"1x": hs >= as_, "12": hs != as_, "x2": hs <= as_}[selection]
    if market.startswith("ou_"):
        line = float(market[3:].replace("_", "."))
        return total > line if selection == "over" else total < line
    if market == "btts":
        both = hs >= 1 and as_ >= 1
        return both if selection == "yes" else not both
    raise ValueError(f"unknown market {market}")


def closing_odds(market: str, selection: str, row) -> float | None:
    """Real closing odds for a selection where the data has them (1X2, O/U 2.5); else None."""
    col = {("1x2", "home"): "odds_home", ("1x2", "draw"): "odds_draw", ("1x2", "away"): "odds_away",
           ("ou_2_5", "over"): "odds_over_2_5", ("ou_2_5", "under"): "odds_under_2_5"}.get((market, selection))
    if col is None:
        return None
    v = row.get(col) if hasattr(row, "get") else getattr(row, col, None)
    return float(v) if v is not None and np.isfinite(v) and v > 1 else None


def rank_by_day(df: pd.DataFrame, tz: str = "Europe/London") -> pd.Series:
    """1-based rank of each pick within its (UK) kickoff day, most likely first."""
    day = pd.to_datetime(df["kickoff"], utc=True).dt.tz_convert(tz).dt.date
    return df.assign(_day=day).groupby("_day")["probability"].rank(ascending=False, method="first").astype(int)


def market_probability(market: str, selection: str, row) -> float | None:
    """The bookmaker's implied chance (closing odds, margin removed) for a selection, where derivable:
    1X2 and double chance from 1X2 odds, O/U 2.5 from O/U odds. None otherwise."""
    g = (lambda c: row.get(c)) if hasattr(row, "get") else (lambda c: getattr(row, c, None))
    if market in ("1x2", "double_chance"):
        o = [g("odds_home"), g("odds_draw"), g("odds_away")]
        if any(v is None or not np.isfinite(v) or v <= 1 for v in o):
            return None
        inv = np.array([1 / v for v in o])
        h, d, a = inv / inv.sum()
        return float({("1x2", "home"): h, ("1x2", "draw"): d, ("1x2", "away"): a, ("double_chance", "1x"): h + d,
                      ("double_chance", "12"): h + a, ("double_chance", "x2"): d + a}[(market, selection)])
    if market == "ou_2_5":
        o, u = g("odds_over_2_5"), g("odds_under_2_5")
        if any(v is None or not np.isfinite(v) or v <= 1 for v in (o, u)):
            return None
        po = (1 / o) / (1 / o + 1 / u)
        return float(po if selection == "over" else 1 - po)
    return None
