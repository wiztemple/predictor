import type { Metadata } from "next";
import Link from "next/link";
import { PicksPanel } from "@/components/PicksPanel";
import { formatShortDay, pct } from "@/lib/format";
import { panelPicks } from "@/lib/panel";
import { MARKET_NAMES, getPicksBacktest, getPicksSummary } from "@/lib/picksRecord";
import { getPredictions } from "@/lib/predictions";

export const metadata: Metadata = { title: "Picks" };

function Tile({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-xl border border-border p-4">
      <div className="text-xs text-text-3">{label}</div>
      <div className="mt-1 text-2xl font-bold tabular">{value}</div>
      {note ? <div className="mt-1 text-xs text-text-3">{note}</div> : null}
    </div>
  );
}

const STATE = {
  won: { icon: "✓", label: "Won", cls: "bg-[#0ca30c] text-white" },
  lost: { icon: "✗", label: "Lost", cls: "bg-[#d03b3b] text-white" },
  void: { icon: "–", label: "Void", cls: "bg-surface-2 text-text-3" },
} as const;

export default async function PicksPage() {
  const [doc, live, bt] = await Promise.all([getPredictions(), getPicksSummary(), getPicksBacktest()]);
  const perDay = bt?.rule.per_day ?? live?.per_day ?? 10;
  const t = live?.top;

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Our likeliest picks</h1>
        <p className="mt-1 max-w-2xl text-sm text-text-2">
          For every match we take the single most likely bet across all markets (result, double chance, over/under,
          both teams to score), then list the top {perDay} each day. Every pick is saved to our database before kickoff
          and settled after the final whistle. Nothing is edited after the fact.
        </p>
      </div>

      <PicksPanel picks={panelPicks(doc.predictions, perDay)} record={null} heading={false} />

      {/* live record */}
      <section>
        <h2 className="text-lg font-bold">Live record</h2>
        {t && t.n > 0 ? (
          <>
            <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Tile label="Picks settled" value={t.n.toLocaleString("en-GB")} note={`since ${live!.first_logged ? formatShortDay(live!.first_logged) : "start"}`} />
              <Tile label="Won" value={`${t.won}/${t.n}`} />
              <Tile label="Hit rate" value={pct(t.hit_rate!)} note={`we predicted ${pct(t.avg_probability!)} on average`} />
              {t.vs_market ? (
                <Tile label="Bookmaker's view" value={pct(t.vs_market.market)} note={`their average chance on ${t.vs_market.n} of these picks (ours ${pct(t.vs_market.ours)})`} />
              ) : (
                <Tile label="Days tracked" value={String(live!.days.length)} />
              )}
            </div>
            {t.n < 100 ? (
              <p className="mt-2 text-xs text-text-3">Still early: with fewer than 100 picks the hit rate can swing a lot.</p>
            ) : null}

            <div className="mt-5 flex flex-wrap gap-2">
              {live!.days.map((d) => (
                <span key={d.day} className="rounded-lg bg-surface-2 px-2.5 py-1.5 text-xs tabular">
                  <span className="text-text-3">{formatShortDay(d.day)}</span>{" "}
                  <span className={d.won === d.n ? "font-bold text-[#0ca30c]" : "font-semibold"}>
                    {d.won}/{d.n}
                  </span>
                </span>
              ))}
            </div>

            <ul className="mt-5 divide-y divide-border rounded-xl border border-border">
              {live!.recent.map((r) => {
                const s = STATE[r.state];
                return (
                  <li key={r.match_id} className="flex items-center gap-3 px-3 py-2.5">
                    <span aria-label={s.label} className={`flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${s.cls}`}>
                      {s.icon}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate font-medium">{r.label}</span>
                      <span className="block truncate text-xs text-text-3">
                        {r.home} {r.score ?? "v"} {r.away} · {formatShortDay(r.kickoff)}
                      </span>
                    </span>
                    <span className="shrink-0 text-sm font-semibold tabular">{pct(r.probability)}</span>
                  </li>
                );
              })}
            </ul>
          </>
        ) : (
          <p className="mt-3 rounded-xl border border-dashed border-border p-6 text-text-2">
            Tracking has started{live?.first_logged ? ` (${formatShortDay(live.first_logged)})` : ""}:{" "}
            {live?.log_entries ? `${live.log_entries} picks saved so far.` : "picks are being saved."} Results appear here
            as matches finish.
          </p>
        )}
      </section>

      {/* backtest */}
      {bt ? (
        <section>
          <h2 className="text-lg font-bold">How this rule did in testing</h2>
          <p className="mt-1 max-w-2xl text-sm text-text-2">
            The same rule replayed over {bt.seasons[0]} to {bt.seasons[bt.seasons.length - 1]}, using only what our
            model knew before each match.
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Tile label="Picks" value={bt.top_per_day.n.toLocaleString("en-GB")} note={`over ${bt.days} match days`} />
            <Tile label="Won" value={pct(bt.top_per_day.hit_rate!)} note={`we predicted ${pct(bt.top_per_day.avg_probability!)}`} />
            <Tile label="Perfect days" value={`${bt.days_all_won}/${bt.days}`} note={`every top-${perDay} pick won`} />
            {bt.top_per_day.vs_market ? (
              <Tile
                label="Bookmaker's view"
                value={pct(bt.top_per_day.vs_market.market)}
                note={`their chance on ${bt.top_per_day.vs_market.n.toLocaleString("en-GB")} double-chance picks (ours ${pct(bt.top_per_day.vs_market.ours)}, won ${pct(bt.top_per_day.vs_market.hit_rate ?? 0)})`}
              />
            ) : null}
          </div>
          <div className="mt-5 grid gap-6 md:grid-cols-2">
            <table className="w-full text-sm tabular">
              <caption className="mb-2 text-left font-semibold">By market</caption>
              <thead>
                <tr className="text-left text-text-3">
                  <th className="py-1 font-normal">Market</th>
                  <th className="py-1 text-right font-normal">Picks</th>
                  <th className="py-1 text-right font-normal">Won</th>
                  <th className="py-1 text-right font-normal">Predicted</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(bt.top_by_market).map(([k, v]) => (
                  <tr key={k} className="border-t border-border">
                    <td className="py-1.5">{MARKET_NAMES[k] ?? k}</td>
                    <td className="py-1.5 text-right">{v.n.toLocaleString("en-GB")}</td>
                    <td className="py-1.5 text-right font-semibold">{pct(v.hit_rate!)}</td>
                    <td className="py-1.5 text-right text-text-2">{pct(v.avg_probability!)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <table className="w-full text-sm tabular">
              <caption className="mb-2 text-left font-semibold">By confidence</caption>
              <thead>
                <tr className="text-left text-text-3">
                  <th className="py-1 font-normal">Our chance</th>
                  <th className="py-1 text-right font-normal">Picks</th>
                  <th className="py-1 text-right font-normal">Won</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(bt.top_by_band).map(([k, v]) => (
                  <tr key={k} className="border-t border-border">
                    <td className="py-1.5">{k}</td>
                    <td className="py-1.5 text-right">{v.n.toLocaleString("en-GB")}</td>
                    <td className="py-1.5 text-right font-semibold">{pct(v.hit_rate!)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 max-w-2xl text-xs text-text-3">
            These picks are mostly double chance, over 1.5 and under 3.5, so the prices are short (roughly 1.10–1.35).
            A high win rate at short odds doesn&apos;t mean profit: bookmakers build their margin into these prices, and
            our historical data has no odds for these markets, so we can&apos;t show a profit figure. See the{" "}
            <Link href="/track-record" className="text-home hover:underline">
              full track record
            </Link>
            .
          </p>
        </section>
      ) : null}
    </div>
  );
}
