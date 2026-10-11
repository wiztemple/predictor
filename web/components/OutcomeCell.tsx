import { fairOdds } from "@/lib/markets";
import { pct } from "@/lib/format";

/** Sportsbook-style cell: option label, our chance, and the fair odds for that chance.
 *  `compact` is the dense version used in the match list. */
export function OutcomeCell({ label, p, best, compact = false }: { label: string; p: number; best: boolean; compact?: boolean }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-md px-1 tabular ${compact ? "py-1" : "py-1.5"} ${
        best ? "bg-surface ring-2 ring-win" : "bg-surface ring-1 ring-border"
      }`}
    >
      <span className={`${compact ? "text-[10px] leading-none" : "text-[11px]"} font-semibold ${best ? "text-win" : "text-text-3"}`}>
        {label}
      </span>
      <span className={`${compact ? "text-sm" : "text-base"} leading-tight font-semibold ${best ? "text-text" : "text-text-2"}`}>
        {pct(p)}
      </span>
      <span className={`${compact ? "text-[10px] leading-none" : "text-[11px]"} text-text-3`}>@{fairOdds(p)}</span>
    </div>
  );
}
