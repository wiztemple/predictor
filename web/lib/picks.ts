import type { BacktestSummary } from "@/lib/trackRecord";

export type Threshold = { min_p: number; n: number; mean_pred: number; hit_rate: number };

/** Win-pick thresholds (home or away win) from the production model's reliability bins. */
export function winThresholds(bt: BacktestSummary | null): Threshold[] {
  const bins = bt?.reliability?.[bt.production_model];
  if (!bins) return [];
  return [0.5, 0.6, 0.7, 0.8].flatMap((t) => {
    const sel = bins.filter((b) => b.outcome !== "draw" && b.bin_lo >= t - 1e-9);
    const n = sel.reduce((s, b) => s + b.n, 0);
    if (!n) return [];
    return [
      {
        min_p: t,
        n,
        mean_pred: sel.reduce((s, b) => s + b.mean_pred * b.n, 0) / n,
        hit_rate: sel.reduce((s, b) => s + b.observed * b.n, 0) / n,
      },
    ];
  });
}

/** Goals-market thresholds for one side ("over" = over / GG, "under" = under / NG). */
export function goalsThresholds(bt: BacktestSummary | null, key: string, side: "over" | "under"): Threshold[] {
  return (bt?.goals_markets?.[key]?.thresholds ?? [])
    .filter((t) => t.direction === side)
    .map(({ min_p, n, mean_pred, hit_rate }) => ({ min_p, n, mean_pred, hit_rate }));
}
