import { readFile } from "node:fs/promises";
import path from "node:path";
import { cache } from "react";

// Written by scripts/backtest.py (data/backtest/summary.json).
export type BacktestRow = {
  model: string;
  label: string;
  league: string; // league code or "ALL"
  n: number;
  log_loss: number;
  brier: number;
  accuracy: number;
};

export type ReliabilityBin = {
  outcome: "home" | "draw" | "away";
  bin_lo: number;
  bin_hi: number;
  n: number;
  mean_pred: number;
  observed: number;
};

export type BacktestSummary = {
  generated_at: string;
  test_seasons: string[];
  n_matches: number;
  production_model: string;
  selection: { blend_weight_elo: number; calibration: Record<string, string>; holdout_season: string };
  rows: BacktestRow[];
  gap_to_bookmaker: Record<string, { mean: number; ci_low: number; ci_high: number }>;
  reliability: Record<string, ReliabilityBin[]>;
  labels: Record<string, string>;
  goals_markets?: Record<string, GoalsMarketBacktest>;
  extra_markets?: Record<string, { label: string; n: number; model: number; baseline: number; ece: number }>;
  half_time_check?: {
    share_45: number;
    n: number;
    model: { log_loss: number; accuracy: number };
    baseline: { log_loss: number; accuracy: number };
    draw_predicted: number;
    draw_actual: number;
  };
  asian_handicap?: {
    n_matches: number;
    predicted: { win: number; push: number; lose: number };
    actual: { win: number; push: number; lose: number };
    profit_at_fair: number;
    vs_bookmaker?: {
      n: number;
      ours: number;
      bookmaker: number;
      gap: { mean: number; ci_low: number; ci_high: number };
      value_bets: Record<string, { n: number; avg_odds: number; profit_units: number; roi: number }>;
    };
  };
};

type BinaryMetrics = { n: number; log_loss: number; brier: number };

export type GoalsMarketBacktest = {
  calibration: string;
  model: BinaryMetrics; // calibrated, as shown on the site
  model_raw: BinaryMetrics;
  baseline: BinaryMetrics;
  ece: number;
  ece_raw: number;
  base_rate: number;
  bookmaker?: {
    n: number;
    model: BinaryMetrics;
    bookmaker: BinaryMetrics;
    gap: { mean: number; ci_low: number; ci_high: number };
  };
  thresholds: { direction: "over" | "under"; min_p: number; n: number; mean_pred: number; hit_rate: number }[];
};

const BACKTEST_PATH =
  process.env.BACKTEST_PATH ?? path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "backtest", "summary.json");

// Missing file = backtest not run yet; the page shows an empty state.
export const getBacktest = cache(async (): Promise<BacktestSummary | null> => {
  try {
    return JSON.parse(await readFile(BACKTEST_PATH, "utf8")) as BacktestSummary;
  } catch {
    return null;
  }
});

// Written by scripts/score_predictions.py from the append-only prediction log.
type Metrics = { n: number; log_loss: number; brier: number; accuracy: number };

export type LiveSummary = {
  generated_at: string;
  primary_model?: string;
  first_logged?: string | null;
  n_logged_matches: number;
  n_scored: number;
  n_pending: number;
  n_void: number;
  model?: Metrics;
  same_matches_with_odds?: { n: number; model: Metrics; bookmaker: Metrics };
  recent: {
    id: string;
    league: string;
    kickoff: string;
    home: string;
    away: string;
    logged_at: string;
    probabilities: { home: number; draw: number; away: number };
    state: "scored" | "pending" | "void";
    score: string | null;
    outcome: "H" | "D" | "A" | null;
  }[];
};

const LIVE_PATH =
  process.env.LIVE_SUMMARY_PATH ??
  path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "predictions", "live_summary.json");

export const getLiveSummary = cache(async (): Promise<LiveSummary | null> => {
  try {
    return JSON.parse(await readFile(LIVE_PATH, "utf8")) as LiveSummary;
  } catch {
    return null;
  }
});

// Written by scripts/backtest_corners.py (data/backtest/corners.json).
export type CornersBacktest = {
  generated_at: string;
  test_seasons: string[];
  n_matches: number;
  benchmark: string;
  mean_total: number;
  mean_predicted: number;
  count_log_loss: { model: number; baseline: number; gain: number; gain_ci: [number, number] };
  lines: Record<
    string,
    {
      line: number;
      base_rate: number;
      model: { n: number; log_loss: number; brier: number };
      baseline: { n: number; log_loss: number; brier: number };
      log_loss_gain: number;
      log_loss_gain_ci: [number, number];
      reliability: { bin_lo: number; bin_hi: number; n: number; mean_pred: number; observed: number }[];
      thresholds: GoalsMarketBacktest["thresholds"];
    }
  >;
};

const CORNERS_PATH = path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "backtest", "corners.json");

export const getCornersBacktest = cache(async (): Promise<CornersBacktest | null> => {
  try {
    return JSON.parse(await readFile(CORNERS_PATH, "utf8")) as CornersBacktest;
  } catch {
    return null;
  }
});
