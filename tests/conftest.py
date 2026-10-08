import numpy as np
import pandas as pd
import pytest

from predictor.schema import outcome_from_scores


def simulate_league(league="XX", n_teams=12, seasons=("2019-20", "2020-21", "2021-22"),
                    home=0.3, mu=0.2, seed=0):
    """Double round-robin seasons with Poisson goals from known strengths."""
    rng = np.random.default_rng(seed)
    teams = [f"T{i:02d}" for i in range(n_teams)]
    attack = np.linspace(0.4, -0.4, n_teams)
    defence = -attack * 0.8  # good teams also concede less
    rows = []
    for s_i, season in enumerate(seasons):
        start = pd.Timestamp(f"{2019 + s_i}-08-10")
        pairs = [(h, a) for h in range(n_teams) for a in range(n_teams) if h != a]
        rng.shuffle(pairs)
        for k, (h, a) in enumerate(pairs):
            date = start + pd.Timedelta(days=7 * (k // (n_teams // 2)))
            lam = np.exp(mu + home + attack[h] + defence[a])
            mu_ = np.exp(mu + attack[a] + defence[h])
            rows.append((league, season, date, teams[h], teams[a], rng.poisson(lam), rng.poisson(mu_)))
    df = pd.DataFrame(rows, columns=["league", "season", "date", "home", "away", "home_score", "away_score"])
    df["sport"] = "football"
    df["outcome"] = outcome_from_scores(df["home_score"], df["away_score"])
    for c in ("odds_home", "odds_draw", "odds_away"):
        df[c] = np.nan
    df = df.sort_values(["date", "league", "home"], kind="stable").reset_index(drop=True)
    return df, dict(teams=teams, attack=attack, defence=defence, home=home, mu=mu)


@pytest.fixture(scope="session")
def sim():
    return simulate_league()


@pytest.fixture(scope="session")
def sim_two_leagues():
    a, _ = simulate_league("AA", seed=1)
    b, _ = simulate_league("BB", seed=2)
    return pd.concat([a, b]).sort_values(["date", "league", "home"], kind="stable").reset_index(drop=True)
