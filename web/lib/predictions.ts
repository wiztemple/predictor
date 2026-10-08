import { readFile } from "node:fs/promises";
import path from "node:path";
import { cache } from "react";

// Mirrors the sport-agnostic schema written by scripts/predict_fixtures.py.
export type Outcome3 = { home: number; draw: number; away: number };

export type Scoreline = { home: number; away: number; p: number };

export type FootballExtras = {
  goals_model?: string;
  /** P(home goals - away goals = i - cap); drives Asian handicap */
  margin?: { cap: number; probs: number[] };
  goals_calibrated?: boolean;
  /** result after 10 minutes - an estimate from expected goals (no goal-time data to verify it) */
  ten_min?: { home: number; draw: number; away: number; no_goal: number };
  expected_goals?: { home: number; away: number };
  over_1_5?: number;
  over_2_5?: number;
  over_3_5?: number;
  btts?: number;
  top_scorelines?: Scoreline[];
  score_grid?: { max_goals: number; cells: number[][]; other: number };
};

export type ModelRef = { name: string; version: string };

export type Prediction = {
  id: string;
  sport: string;
  league: string;
  league_name: string;
  season: string;
  kickoff: string;
  kickoff_tbc: boolean;
  home: string;
  away: string;
  probabilities: Outcome3;
  extras: FootballExtras;
  model: ModelRef;
  other_models: (ModelRef & { probabilities: Outcome3 })[];
  /** the single most likely selection across all markets, and its rank within its UK day */
  best_pick?: { market: string; selection: string; label: string; p: number; day_rank: number };
  fixture_source: string;
  generated_at: string;
};

export type Unmatched = {
  league: string;
  kickoff: string;
  fixture: string;
  unmatched_name: string;
  source: string;
  suggestions: string[];
};

export type PredictionsDoc = {
  schema_version: string;
  generated_at: string;
  status: "preview" | "validated";
  data_through: string;
  leagues: { code: string; name: string; sport: string }[];
  predictions: Prediction[];
  unmatched: Unmatched[];
};

const PREDICTIONS_PATH =
  process.env.PREDICTIONS_PATH ??
  path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "predictions", "predictions.json");

// Read once per request/build; every page shares the parsed document.
export const getPredictions = cache(async (): Promise<PredictionsDoc> => {
  const raw = await readFile(PREDICTIONS_PATH, "utf8");
  const doc = JSON.parse(raw) as PredictionsDoc;
  doc.predictions.sort((a, b) => a.kickoff.localeCompare(b.kickoff));
  return doc;
});

export async function getLeague(code: string) {
  const doc = await getPredictions();
  const league = doc.leagues.find((l) => l.code === code);
  if (!league) return null;
  return { league, matches: doc.predictions.filter((p) => p.league === code) };
}

export async function getMatch(id: string) {
  const doc = await getPredictions();
  return doc.predictions.find((p) => p.id === id) ?? null;
}
