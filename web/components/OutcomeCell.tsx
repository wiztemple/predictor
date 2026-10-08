import { fairOdds } from "@/lib/markets";
import { pct } from "@/lib/format";

/** Sportsbook-style cell: option label, our chance, and the fair odds for that chance. */
export function OutcomeCell({ label, p, best }: { label: string; p: number; best: boolean }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-md px-1 py-1.5 tabular ${
        best ? "bg-home/12 ring-1 ring-home" : "bg-surface-2"
      }`}
    >
      <span className={`text-[11px] font-medium ${best ? "text-home" : "text-text-3"}`}>{label}</span>
      <span className={`text-base leading-tight font-semibold ${best ? "text-text" : "text-text-2"}`}>{pct(p)}</span>
      <span className="text-[11px] text-text-3">@{fairOdds(p)}</span>
    </div>
  );
}
