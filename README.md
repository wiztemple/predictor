# predictor

Match outcome predictions, built from historical results and bookmaker odds.
Football is the first sport. There are 21 leagues, all using data from
[football-data.co.uk](https://www.football-data.co.uk):

- **Top divisions:** Premier League (E0), La Liga (SP1), Serie A (I1),
  Bundesliga (D1), Ligue 1 (F1), Eredivisie (N1), Primeira Liga (P1), Scottish
  Premiership (SC0), Belgian Pro League (B1), Süper Lig (T1) and Greek Super
  League (G1)
- **Second divisions:** Championship (E1), La Liga 2 (SP2), Serie B (I2),
  Bundesliga 2 (D2) and Ligue 2 (F2)
- **"Extra leagues":** Romania (ROU), Austria (AUT), Switzerland (SWZ),
  Denmark (DNK) and Poland (POL)

**Extra leagues.** football-data.co.uk publishes these in a different
layout: one `new/{CODE}.csv` per league holding every season, closing
win/draw/loss odds only (no over/under odds), and a separate fixtures list,
`new_league_fixtures.csv`. `loaders/football_data_extra.py` reads that layout.

To add another extra league:

1. Add an entry to `football_data.extra_leagues` with the country and league
   name exactly as the file spells them.
2. Add a display name to `football_data.leagues`.
3. Add the code to the country list in `web/lib/leagues.ts`.

Only leagues whose season runs August to May are supported. Calendar-year
leagues such as Norway, Sweden, Brazil and USA need season handling first, and
the loader refuses their season labels.

**Club renames.** Clubs that changed name are mapped to their current name in
`football_data.team_renames`. Examples: U Craiova → Univ. Craiova, Gornik Z.
→ Gornik Zabrze.

**Relegated clubs.** `football_data.tiers` in `config.yaml` links each second
division to the league above it. When a club drops down, both models give it a
strong starting estimate in its new league. The Elo setting for this,
`relegated_offset`, was tuned on the pre-test seasons. Promoted clubs still
start weak.

**Forfeits.** Forfeited results, such as the Turkish 2022-23 matches awarded
after the earthquake withdrawals, are listed in
`football_data.excluded_matches` and dropped from the data.

**Fixture coverage.** Fixtures for D2, I2, SP2, B1 and G1 come only from
football-data's `fixtures.csv`, and fixtures for the extra leagues only from
`new_league_fixtures.csv`. Both list matches just a few days ahead.

The models run offline in Python. A frontend (later) only displays the
predictions they have already computed.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

## Data pipeline

```bash
.venv/bin/python scripts/download_data.py   # raw CSVs -> data/raw/football/{league}_{season}.csv
.venv/bin/python scripts/build_dataset.py   # merged table -> data/processed/matches.parquet
.venv/bin/python scripts/check_data.py      # coverage report + warnings
.venv/bin/python -m pytest
```

Completed seasons are downloaded once. The current season is re-downloaded
on every run. Use `--force` to re-download everything.

## Layout

| Path | Purpose |
| --- | --- |
| `config.yaml` | All tunable settings: leagues, seasons, URLs, odds priority |
| `src/predictor/schema.py` | Shared match schema that every sport uses |
| `src/predictor/loaders/football_data.py` | Turns football-data CSVs into schema rows |
| `scripts/` | Command-line entry points |
| `tests/` | Unit tests |

## Match schema

Every sport's loader produces these columns:

`sport, league, season, date, home, away, home_score, away_score, outcome (H/D/A), odds_home, odds_draw, odds_away`

It may also add `odds_source`, which records which bookmaker's prices were used.

The odds for each match are the first complete set of three prices found in
this order. Closing odds are preferred to opening odds.

1. Pinnacle closing
2. Market-average closing
3. Bet365 closing
4. Pinnacle opening
5. Market-average opening
6. Bet365 opening

Prices of 1.0 or less count as missing.

## Data notes

- **No Pinnacle odds after mid 2025-26.** football-data.co.uk stopped
  publishing Pinnacle closing odds partway through 2025-26. Later matches use
  market-average closing odds. Their margin is about 6.4%, against about 2.8%
  for Pinnacle, which makes them a weaker benchmark for the newest data.
- **2019-20 F1 and N1 are incomplete.** Ligue 1 and the Eredivisie cancelled
  the end of that season because of COVID, so those files are short.

## Models (Step 2)

Every model implements `fit(matches, as_of=cutoff)` and `predict(fixtures)`.
`fit` trains only on matches dated before the cutoff. `predict` returns
`p_home, p_draw, p_away` plus whatever extra markets the model supports.
`predict` raises `LeakageError` for any fixture dated on or before the last
training match.

- **Elo** (`models/elo.py`, built on the sport-agnostic `ratings/elo.py`).
  Ratings use a home advantage, a K-factor and the World Football Elo
  goal-difference multiplier. Promoted or new teams start at the league mean
  plus an offset. The rating difference becomes home/draw/away probabilities
  through a per-league ordered logit (`models/ordered_logit.py`) fitted on
  pre-match rating differences.
- **Dixon-Coles** (`models/dixon_coles.py`), fitted per league. It has attack
  and defence strengths for each team, a home advantage, the low-score
  correction rho, exponential time decay and a ridge penalty. It is fitted by
  L-BFGS with an analytic gradient. It returns the full scoreline grid, which
  gives 1X2, over/under 2.5, both teams to score and the top scorelines.

Hyperparameters are tuned by walk-forward log loss on `evaluation.tune_seasons`
only:

```bash
.venv/bin/python scripts/tune_models.py --model elo
.venv/bin/python scripts/tune_models.py --model dixon_coles
```

## Predictions (Step 4)

```bash
.venv/bin/python scripts/predict_fixtures.py                    # online fixture sources
.venv/bin/python scripts/predict_fixtures.py --fixtures my.csv  # add your own fixtures CSV
```

The script writes `data/predictions/predictions.json`, with one record per match
in a sport-agnostic format. Each record has `sport, league, kickoff, home, away`,
the home/draw/away probabilities, extra markets (over 2.5, both teams to score,
top scorelines and the score grid), the model name and version, and
`generated_at`. The models predict fixtures in the next `fixtures.horizon_days`
days. Fixtures come from three sources. When the same match appears in more
than one, the earlier source in this list wins:

1. a CSV you pass with `--fixtures`
2. football-data `fixtures.csv`
3. fixturedownload.com season schedules

`team_names.yaml` maps external team names to the names used in the historical
data. Matching uses only exact names and this hand-reviewed table. Unknown
names are listed in the script output and in the JSON's `unmatched` list,
never guessed. To fix one, add an entry to `team_names.yaml`.

`predictions.status` in `config.yaml` stays `preview` until the Step 3 backtest
looks reasonable. While it does, the site shows an "unvalidated" banner.

## Frontend (Step 5)

The Next.js frontend is in `web/`. See `web/README.md`.

```bash
cd web && pnpm install && pnpm dev   # http://localhost:3000
```

## Backtest and calibration (Step 3)

```bash
.venv/bin/python scripts/backtest.py            # reuses cached walk-forward predictions (~10 s)
.venv/bin/python scripts/backtest.py --refresh  # recompute everything (~50 s)
```

The script writes the following to `data/backtest/`:

- `report.md`: the full write-up
- `summary.json`: read by the frontend's track record page
- `predictions.parquet`: every test-period prediction from every model

**How the test was run.** Every week from 2020-21 onward was predicted with
models fitted only on earlier matches. The blend weight, the calibration method
and the production model were all chosen on seasons before 2023-24. The test
seasons, 2023-24 to 2026-27, were used only to measure results. Each test
season's calibrator was fitted only on predictions from earlier seasons.

**Result.** No model beats the bookmaker's closing odds:

| Model | Log loss |
| --- | --- |
| Bookmaker closing odds | 0.960 |
| Production blend (40% Elo + 60% Dixon-Coles) | 0.980 |

The gap is +0.020, with a 95% interval of +0.016 to +0.023. The blend is well
calibrated, with an expected calibration error of about 0.01 per outcome, so
recalibration didn't help.

## Automation and live track record (Step 6)

```bash
scripts/update.sh   # download -> build -> check -> predict + log -> score
```

To schedule it with cron:

```
30 5 * * *    cd /path/to/predictor && scripts/update.sh >> data/update.log 2>&1
30 10 * * 5-7 cd /path/to/predictor && scripts/update.sh >> data/update.log 2>&1
```

`.github/workflows/update.yml` runs the same pipeline on GitHub Actions. It
runs every day at 05:30 UTC, and again at 10:30 UTC from Friday to Sunday. It
also runs the tests first, refreshes the backtest on Mondays, commits
`data/predictions/` back to the repo and checks that the site still builds.

**Prediction log.** Predictions are written to `data/predictions/log/YYYY-MM.jsonl`:

- A prediction is logged only if its match hasn't kicked off.
- The log is append-only.
- A re-run with unchanged numbers adds nothing.
- Each committed version of the log is timestamped by git, which gives an
  audit trail.

**Scoring.** `scripts/score_predictions.py` scores the latest prediction logged
before each kickoff. It writes the results to
`data/predictions/live_summary.json`, alongside the bookmaker's closing odds on
the same matches.

- A result counts only if it was played within a day of the logged kickoff.
- A match still unplayed three days after its logged kickoff is marked void,
  because it was postponed. The rearranged match gets a fresh prediction before
  its new date.

**Fixture feeds.** Each schedule feed is retried, and the last good copy is
cached in `data/raw/fixtures/`. If a feed is down, the pipeline falls back to
that copy and logs a warning, so a league doesn't silently disappear.

### Goals markets

`scripts/backtest.py` also backtests over/under 1.5, 2.5 and 3.5 and both
teams to score, using the Dixon-Coles probabilities. It compares them with
each league's past rate and, for the 2.5 line, with the bookmaker's closing
over/under odds (football-data `PC>2.5` and similar columns).

**Calibration.** Each market is calibrated with no calibration, Platt or
isotonic. The method was chosen on 2022-23, before the test period, and Platt
won for every market. During the backtest, each season is calibrated using
only earlier seasons. The live pipeline uses
`data/models/goals_calibration.json`, which is fitted on every out-of-sample
prediction so far and refreshed whenever the backtest runs. After calibrating,
the pipeline keeps the three lines consistent, so P(over 1.5) ≥ P(over 2.5) ≥
P(over 3.5). The scoreline grid and expected goals stay uncalibrated.

## Likeliest picks (tracked)

For each match, a **pick** is the single most likely selection across 1X2,
double chance, O/U 1.5, 2.5 and 3.5, and both teams to score. The top 10 per
UK day (`picks.per_day`) are the list we publish and track. The rule lives in
`src/predictor/picks.py`, and the live site, the database and the backtest all
use it.

**Storage.** `src/predictor/store.py` uses SQLAlchemy and two tables:

- `picks_log`: append-only. Every pick is logged before kickoff and never
  updated.
- `official_picks`: one row per finished match. It holds the latest pick logged
  before kickoff, settled as won, lost or void, with the score, the closing
  odds and the bookmaker's implied chance where the data has them.

**Local credentials.** Put `DATABASE_URL=postgresql://...` in `.env` at the
project root. The scripts read it automatically, and real environment
variables take priority over it. `.env` is gitignored, so never commit it.

**Choosing the database.**

- **Production:** set `DATABASE_URL`. Postgres URLs (`postgres://` or
  `postgresql://`) are accepted as-is. On GitHub Actions, store it as a repo
  secret called `DATABASE_URL`.
- **Without it:** a local SQLite file, `data/picks/picks.db`, is used.
- **Switching over:** run `DATABASE_URL=... python scripts/migrate_picks.py`
  once to copy the local picks into the new database. It's safe to run more
  than once.

**Pipeline.**

- `predict_fixtures.py` logs the picks.
- `settle_picks.py` settles finished matches and writes
  `data/picks/summary.json`, which the site reads.
- `backtest_picks.py` replays the rule over the test seasons and writes
  `data/picks/backtest.json`.
