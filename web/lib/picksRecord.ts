import { readFile } from "node:fs/promises";
import path from "node:path";
import { cache } from "react";

type Stats = {
  n: number;
  won: number;
  hit_rate?: number;
  avg_probability?: number;
  vs_market?: { n: number; ours: number; market: number; hit_rate?: number };
  priced?: { n: number; profit_units: number; roi: number };
};

/** Live record exported from the picks database by scripts/settle_picks.py. */
export type PicksSummary = {
  generated_at: string;
  per_day: number;
  log_entries: number;
  first_logged: string | null;
  settled: number;
  top: Stats;
  by_market: Record<string, Stats>;
  days: { day: string; n: number; won: number }[];
  recent: {
    match_id: string;
    league: string;
    kickoff: string;
    home: string;
    away: string;
    label: string;
    market: string;
    probability: number;
    state: "won" | "lost" | "void";
    score: string | null;
  }[];
};

/** Same rule replayed over the test seasons by scripts/backtest_picks.py. */
export type PicksBacktest = {
  rule: { markets: string[]; per_day: number };
  seasons: string[];
  top_per_day: Stats;
  top_by_market: Record<string, Stats>;
  top_by_band: Record<string, Stats>;
  days: number;
  days_all_won: number;
  weekly_lists?: Record<string, WeeklyBacktest>;
};

const DIR = path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "picks");

async function read<T>(file: string): Promise<T | null> {
  try {
    return JSON.parse(await readFile(path.join(/*turbopackIgnore: true*/ DIR, file), "utf8")) as T;
  } catch {
    return null;
  }
}

export const getPicksSummary = cache(() => read<PicksSummary>("summary.json"));
export const getPicksBacktest = cache(() => read<PicksBacktest>("backtest.json"));

export const MARKET_NAMES: Record<string, string> = {
  "1x2": "Match result",
  double_chance: "Double chance",
  ou_1_5: "Over/Under 1.5",
  ou_2_5: "Over/Under 2.5",
  ou_3_5: "Over/Under 3.5",
  btts: "Both teams to score",
};

/** Weekly lists (Tue-Mon, locked once), exported from the picks database by scripts/settle_picks.py. */
export type PickState = "pending" | "won" | "lost" | "void" | "push" | "half_won" | "half_lost";
export type WeeklyPick = {
  rank: number;
  match_id: string;
  league: string;
  kickoff: string;
  home: string;
  away: string;
  market: string;
  selection: string;
  label: string;
  probability: number;
  state: PickState;
  score: string | null;
};
export type WeeklyList = {
  week_start: string;
  week_end: string;
  locked_at: string;
  picks: WeeklyPick[];
} & Record<PickState, number>;
export type WeeklyListSummary = {
  label: string;
  description: string;
  weeks: WeeklyList[];
  record: { weeks: number; picks: number; won: number; half_won: number; perfect_weeks: number };
};
export type WeeklySummary = { generated_at: string; lists: Record<string, WeeklyListSummary> };
export type WeeklyBacktest = {
  label: string;
  n: number;
  hit_rate: number;
  avg_probability: number;
  avg_fair_odds: number;
  weeks: number;
  perfect_weeks: number;
  avg_won_per_week: number;
  won_distribution: Record<string, number>;
  calibration_gap: number;
  priced?: { n: number; avg_odds: number; profit_units: number; roi: number; roi_ci: [number, number] };
};

export const getWeekly = cache(() => read<WeeklySummary>("weekly.json"));
