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
