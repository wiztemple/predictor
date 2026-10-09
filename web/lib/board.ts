import type { TrackTables } from "@/components/MatchBoard";
import type { BoardMatch } from "@/lib/markets";
import { goalsThresholds, winThresholds } from "@/lib/picks";
import type { Prediction } from "@/lib/predictions";
import type { BacktestSummary, CornersBacktest } from "@/lib/trackRecord";
import { CORNER_LINES } from "@/lib/markets";

/** Only what the board needs, so pages stay light on phones. */
export function toBoardMatch(m: Prediction): BoardMatch {
  return {
    id: m.id, league: m.league, league_name: m.league_name, kickoff: m.kickoff, kickoff_tbc: m.kickoff_tbc,
    home: m.home, away: m.away, probabilities: m.probabilities,
    over_1_5: m.extras.over_1_5, over_2_5: m.extras.over_2_5, btts: m.extras.btts,
    scores: (m.extras.top_scorelines ?? []).slice(0, 3),
    margin: m.extras.margin,
    ten: m.extras.ten_min,
    ht: m.extras.markets?.ht_result,
    dnb: m.extras.markets?.dnb,
    corners: m.extras.corners ? { total: m.extras.corners.expected.total, over: m.extras.corners.over } : undefined,
  };
}

export function trackTables(bt: BacktestSummary | null, corners: CornersBacktest | null = null): TrackTables {
  const crn: TrackTables = {};
  for (const l of CORNER_LINES) {
    const t = corners?.lines[`over_${l.replace(".", "_")}`]?.thresholds ?? [];
    const pick = (side: "over" | "under") =>
      t.filter((r) => r.direction === side).map(({ min_p, n, mean_pred, hit_rate }) => ({ min_p, n, mean_pred, hit_rate }));
    crn[`c${l}` as keyof TrackTables] = { over: pick("over"), under: pick("under") };
  }
  return {
    ...crn,
    "1x2": { over: winThresholds(bt) },
    o15: { over: goalsThresholds(bt, "over_1_5", "over"), under: goalsThresholds(bt, "over_1_5", "under") },
    o25: { over: goalsThresholds(bt, "over_2_5", "over"), under: goalsThresholds(bt, "over_2_5", "under") },
    gg: { over: goalsThresholds(bt, "btts", "over"), under: goalsThresholds(bt, "btts", "under") },
  };
}
