import type { PanelPick } from "@/components/PicksPanel";
import type { Prediction } from "@/lib/predictions";
import type { PicksBacktest, PicksSummary } from "@/lib/picksRecord";
import { pct } from "@/lib/format";

/** Tracked picks (top N per day) from predictions.json, in the panel's slim shape. */
export function panelPicks(predictions: Prediction[], perDay: number): PanelPick[] {
  return predictions
    .filter((m) => m.best_pick && m.best_pick.day_rank <= perDay)
    .map((m) => ({
      id: m.id, kickoff: m.kickoff, kickoff_tbc: m.kickoff_tbc, league_name: m.league_name,
      home: m.home, away: m.away, label: m.best_pick!.label, market: m.best_pick!.market,
      p: m.best_pick!.p, rank: m.best_pick!.day_rank,
    }));
}

/** One-line record: live if there is one, otherwise the backtest. */
export function recordLine(live: PicksSummary | null, bt: PicksBacktest | null): string | null {
  if (live && live.top.n >= 20 && live.top.hit_rate !== undefined) {
    return `Live record: ${live.top.won}/${live.top.n} won (${pct(live.top.hit_rate)}).`;
  }
  if (bt?.top_per_day.hit_rate !== undefined) {
    return `In testing over ${bt.seasons.length} seasons, ${pct(bt.top_per_day.hit_rate)} of these picks won (${bt.top_per_day.n.toLocaleString("en-GB")} picks).`;
  }
  return null;
}
