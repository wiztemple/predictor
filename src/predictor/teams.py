"""Map external team names to the canonical names in the historical data.

Matching is exact-or-alias only. Close matches are offered as suggestions
for a human to add to team_names.yaml, never applied automatically.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


@dataclass
class TeamNameMapper:
    known: dict[str, set[str]]                     # league -> canonical team names
    aliases: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_history(cls, matches: pd.DataFrame, alias_file: Path, sport: str = "football") -> "TeamNameMapper":
        known: dict[str, set[str]] = {}
        for league, g in matches.groupby("league"):
            known[league] = set(g["home"]) | set(g["away"])
        aliases = {}
        if Path(alias_file).exists():
            aliases = (yaml.safe_load(Path(alias_file).read_text()) or {}).get(sport) or {}
        return cls(known, {str(k): str(v) for k, v in aliases.items()})

    def match(self, league: str, name: str) -> str | None:
        teams = self.known.get(league, set())
        name = name.strip()
        if name in teams:
            return name
        canonical = self.aliases.get(name)
        if canonical in teams:
            return canonical
        return None

    def suggest(self, league: str, name: str, n: int = 3) -> list[str]:
        teams = sorted(self.known.get(league, set()))
        by_norm = {_norm(t): t for t in teams}
        hits = difflib.get_close_matches(_norm(name), list(by_norm), n=n, cutoff=0.3)
        return [by_norm[h] for h in hits]

    def unknown_aliases(self) -> dict[str, str]:
        """Alias targets that don't exist in any league's history (typos in the yaml)."""
        everything = set().union(*self.known.values()) if self.known else set()
        return {k: v for k, v in self.aliases.items() if v not in everything}
