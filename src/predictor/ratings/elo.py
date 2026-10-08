"""Sport-agnostic Elo rating table.

Knows nothing about goals, draws or leagues: callers pass a result score in
[0, 1] (1 = home win, 0.5 = draw) and an optional multiplier for the size of
the win. The football model supplies a goal-difference multiplier; tennis
could pass a set/game margin, basketball a points margin.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EloRatings:
    k: float = 20.0
    home_advantage: float = 0.0
    initial: float = 1500.0
    scale: float = 400.0
    ratings: dict[str, float] = field(default_factory=dict)

    def get(self, team: str, default: float | None = None) -> float:
        return self.ratings.get(team, self.initial if default is None else default)

    def set(self, team: str, rating: float) -> None:
        self.ratings[team] = rating

    def diff(self, home: str, away: str, neutral: bool = False) -> float:
        """Home rating minus away rating, including home advantage."""
        hfa = 0.0 if neutral else self.home_advantage
        return self.get(home) + hfa - self.get(away)

    def expected(self, diff: float) -> float:
        """Expected score for the side with rating advantage `diff`."""
        return 1.0 / (1.0 + 10.0 ** (-diff / self.scale))

    def update(
        self, home: str, away: str, score: float, multiplier: float = 1.0, neutral: bool = False
    ) -> float:
        """Apply one result. Returns the pre-match diff. Points are zero-sum."""
        d = self.diff(home, away, neutral)
        delta = self.k * multiplier * (score - self.expected(d))
        self.ratings[home] = self.get(home) + delta
        self.ratings[away] = self.get(away) - delta
        return d
