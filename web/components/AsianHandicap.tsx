import { type Margin, ahChance, ahFairOdds, awayOf, fmtLine, homeOutcome, mainLine } from "@/lib/handicap";
import { pct } from "@/lib/format";

/** Handicap table around the main line: each side's push-adjusted chance and fair odds. */
export function AsianHandicap({ margin, home, away }: { margin: Margin; home: string; away: string }) {
  const main = mainLine(margin);
  const lines = Array.from({ length: 9 }, (_, i) => main + (i - 4) * 0.25);
  return (
    <div className="rounded-xl border border-border p-3">
      <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">Asian handicap</h3>
        <span className="text-[11px] text-text-3">Main line highlighted · whole lines can push (stake back)</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm tabular">
          <thead>
            <tr className="text-left text-[11px] text-text-3">
              <th className="py-1 font-normal">{home}</th>
              <th className="py-1 text-right font-normal">Chance</th>
              <th className="py-1 text-right font-normal">Fair</th>
              <th className="py-1 pl-4 font-normal">{away}</th>
              <th className="py-1 text-right font-normal">Chance</th>
              <th className="py-1 text-right font-normal">Fair</th>
              <th className="py-1 text-right font-normal">Push</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line) => {
              const h = homeOutcome(margin, line);
              const a = awayOf(h);
              const isMain = Math.abs(line - main) < 1e-9;
              return (
                <tr key={line} className={`border-t border-border ${isMain ? "bg-home/10 font-semibold" : ""}`}>
                  <td className="py-1.5">{fmtLine(line)}</td>
                  <td className="py-1.5 text-right">{pct(ahChance(h))}</td>
                  <td className="py-1.5 text-right">@{ahFairOdds(h).toFixed(2)}</td>
                  <td className="py-1.5 pl-4">{fmtLine(-line)}</td>
                  <td className="py-1.5 text-right">{pct(ahChance(a))}</td>
                  <td className="py-1.5 text-right">@{ahFairOdds(a).toFixed(2)}</td>
                  <td className="py-1.5 text-right text-text-3">{h.push > 0.0005 ? pct(h.push) : "–"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[11px] text-text-3">
        Chance = 1 ÷ fair odds, which accounts for pushes and half-wins, so it compares directly with other markets.
      </p>
    </div>
  );
}
