import type { LiveSummary } from "@/lib/trackRecord";
import { formatShortDay, pct } from "@/lib/format";

const OUTCOME_KEY = { H: "home", D: "draw", A: "away" } as const;

function stateLabel(r: LiveSummary["recent"][number]) {
  if (r.state === "pending") return <span className="text-text-3">Not played yet</span>;
  if (r.state === "void") return <span className="text-text-3">Postponed</span>;
  return <span className="font-medium">{r.score}</span>;
}

export function LiveRecord({ live, leagueName }: { live: LiveSummary; leagueName: Map<string, string> }) {
  const since = live.first_logged ? formatShortDay(live.first_logged) : null;
  const cmp = live.same_matches_with_odds;

  return (
    <div className="space-y-5">
      <p className="max-w-2xl text-text-2">
        Every prediction is saved to an append-only log before kickoff. The latest one saved before kickoff is the one
        that counts. {since ? `Logging started ${since}. ` : ""}
        {live.n_logged_matches.toLocaleString("en-GB")} matches logged: {live.n_scored.toLocaleString("en-GB")} played,{" "}
        {live.n_pending.toLocaleString("en-GB")} still to play
        {live.n_void ? `, ${live.n_void} postponed` : ""}.
      </p>

      {cmp && cmp.n > 0 ? (
        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-border p-4">
            <div className="text-sm text-text-2">Log loss: ours</div>
            <div className="mt-1 text-2xl font-semibold tabular">{cmp.model.log_loss.toFixed(3)}</div>
            <div className="mt-1 text-xs text-text-3">{cmp.n} played matches</div>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="text-sm text-text-2">Log loss: bookmaker</div>
            <div className="mt-1 text-2xl font-semibold tabular">{cmp.bookmaker.log_loss.toFixed(3)}</div>
            <div className="mt-1 text-xs text-text-3">Same matches, closing odds</div>
          </div>
          <div className="rounded-lg border border-border p-4">
            <div className="text-sm text-text-2">Most likely outcome happened</div>
            <div className="mt-1 text-2xl font-semibold tabular">{pct(cmp.model.accuracy)}</div>
            <div className="mt-1 text-xs text-text-3">Bookmaker: {pct(cmp.bookmaker.accuracy)}</div>
          </div>
        </div>
      ) : (
        <p className="rounded-lg border border-dashed border-border p-4 text-sm text-text-2">
          No logged match has been played yet. Scores appear here once results come in.
        </p>
      )}
      {cmp && cmp.n > 0 && cmp.n < 300 ? (
        <p className="text-xs text-text-3">
          With only {cmp.n} matches, these numbers are still mostly noise. The backtest above is the better guide for
          now.
        </p>
      ) : null}

      {live.recent.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal">Date</th>
                <th className="py-1 font-normal">Match</th>
                <th className="py-1 text-right font-normal">Home / Draw / Away</th>
                <th className="py-1 text-right font-normal">Result</th>
                <th className="py-1 text-right font-normal">Chance we gave the result</th>
              </tr>
            </thead>
            <tbody>
              {live.recent.map((r) => (
                <tr key={r.id} className="border-t border-border">
                  <td className="py-1.5 whitespace-nowrap text-text-2">{formatShortDay(r.kickoff)}</td>
                  <td className="py-1.5">
                    {r.home} vs {r.away}
                    <span className="ml-1.5 text-xs text-text-3">{leagueName.get(r.league) ?? r.league}</span>
                  </td>
                  <td className="py-1.5 text-right whitespace-nowrap">
                    {pct(r.probabilities.home)} / {pct(r.probabilities.draw)} / {pct(r.probabilities.away)}
                  </td>
                  <td className="py-1.5 text-right whitespace-nowrap">{stateLabel(r)}</td>
                  <td className="py-1.5 text-right">
                    {r.outcome ? pct(r.probabilities[OUTCOME_KEY[r.outcome]]) : "–"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
