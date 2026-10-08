import type { Metadata } from "next";
import Link from "next/link";
import { TeamBadge } from "@/components/ui";
import { formatShortDay, formatTime, pct } from "@/lib/format";
import { fairOdds } from "@/lib/markets";
import { type WeeklyList, MARKET_NAMES, getPicksBacktest, getWeekly } from "@/lib/picksRecord";

export const metadata: Metadata = { title: "Weekly top 10" };

const STATE = {
  pending: { text: "To play", pill: "bg-surface-2 text-text-2 ring-border", seg: "bg-border" },
  won: { text: "Won ✓", pill: "bg-win/12 text-win ring-win/30", seg: "bg-win" },
  lost: { text: "Lost ✗", pill: "bg-[#d03b3b]/10 text-[#b42323] ring-[#d03b3b]/30", seg: "bg-[#d03b3b]" },
  void: { text: "Void", pill: "bg-surface-2 text-text-3 ring-border", seg: "bg-text-3/40" },
} as const;

const weekLabel = (w: WeeklyList) => `${formatShortDay(w.week_start)} – ${formatShortDay(w.week_end)}`;

function Progress({ w }: { w: WeeklyList }) {
  return (
    <div className="flex gap-1" aria-hidden>
      {w.picks.map((p) => (
        <span key={p.rank} className={`h-2 flex-1 rounded-full ${STATE[p.state].seg}`} />
      ))}
    </div>
  );
}

function WeekCard({ w, current }: { w: WeeklyList; current: boolean }) {
  const settled = w.won + w.lost;
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-bold">
          {current ? "This week" : "Week"} · {weekLabel(w)}
        </h2>
        <p className="text-sm font-semibold tabular">
          {w.won} won · {w.lost} lost{w.void ? ` · ${w.void} void` : ""}
          {w.pending ? ` · ${w.pending} to play` : ""}
        </p>
      </div>
      <div className="mt-3">
        <Progress w={w} />
      </div>
      {settled === 0 && w.pending ? (
        <p className="mt-2 text-xs text-text-3">Locked {formatShortDay(w.locked_at)} {formatTime(w.locked_at)}. Results appear as matches finish.</p>
      ) : null}
      <ol className="mt-4 divide-y divide-border">
        {w.picks.map((p) => (
          <li key={p.rank} className="flex min-w-0 items-center gap-3 py-2.5">
            <span className="w-5 shrink-0 text-center text-sm font-bold text-text-3 tabular">{p.rank}</span>
            <span className="min-w-0 flex-1">
              <span className="block truncate font-semibold">{p.label}</span>
              <span className="mt-0.5 flex min-w-0 items-center gap-1.5 text-xs text-text-3">
                <TeamBadge name={p.home} />
                <span className="truncate">
                  {p.home} {p.score ? <strong className="text-text">{p.score}</strong> : "v"} {p.away} ·{" "}
                  {formatShortDay(p.kickoff)} · {MARKET_NAMES[p.market] ?? p.market}
                </span>
              </span>
            </span>
            <span className="shrink-0 text-right tabular">
              <span className="block font-bold">{pct(p.probability)}</span>
              <span className="block text-[11px] text-text-3">@{fairOdds(p.probability)}</span>
            </span>
            <span className={`w-16 shrink-0 rounded-full px-2 py-0.5 text-center text-[11px] font-semibold ring-1 ${STATE[p.state].pill}`}>
              {STATE[p.state].text}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export default async function WeeklyPage() {
  const [weekly, bt] = await Promise.all([getWeekly(), getPicksBacktest()]);
  const weeks = weekly?.weeks ?? [];
  const [current, ...past] = weeks;
  const rec = weekly?.record;
  const wb = bt?.weekly;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Weekly top 10</h1>
        <p className="mt-1 max-w-2xl text-sm text-text-2">
          Our 10 likeliest bets of the week, across all markets. The list covers Tuesday to Monday. It&apos;s picked at
          the start of the week from matches not yet played, saved to our database, and never changed after that.
          Each pick is settled when its match finishes.
        </p>
      </div>

      {current ? (
        <WeekCard w={current} current />
      ) : (
        <p className="rounded-2xl border border-dashed border-border p-6 text-text-2">
          This week&apos;s list hasn&apos;t been locked yet. It&apos;s picked at the first update of the week.
        </p>
      )}

      {rec && rec.weeks > 0 ? (
        <section>
          <h2 className="text-lg font-bold">Live record</h2>
          <p className="mt-1 text-sm text-text-2 tabular">
            {rec.weeks} finished week{rec.weeks === 1 ? "" : "s"} · {rec.won}/{rec.picks} picks won
            {rec.picks ? ` (${pct(rec.won / rec.picks)})` : ""} · all 10 won in {rec.perfect_weeks} week
            {rec.perfect_weeks === 1 ? "" : "s"}
          </p>
        </section>
      ) : null}

      {past.length ? (
        <section className="space-y-3">
          <h2 className="text-lg font-bold">Past weeks</h2>
          {past.map((w) => (
            <details key={w.week_start} className="rounded-2xl border border-border bg-surface p-4">
              <summary className="flex cursor-pointer flex-wrap items-center justify-between gap-2 font-semibold">
                <span>{weekLabel(w)}</span>
                <span className="tabular">
                  {w.won}/{w.won + w.lost} won{w.void ? ` · ${w.void} void` : ""}
                </span>
              </summary>
              <div className="mt-3">
                <WeekCard w={w} current={false} />
              </div>
            </details>
          ))}
        </section>
      ) : null}

      {wb ? (
        <section className="rounded-2xl border border-border bg-surface p-4 sm:p-5">
          <h2 className="text-lg font-bold">How this rule did in testing</h2>
          <p className="mt-1 max-w-2xl text-sm text-text-2">
            The same rule replayed over {wb.weeks} weeks (2023-24 to now), using only what our model knew at the start
            of each week.
          </p>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
            {[
              ["Picks won", pct(wb.hit_rate), `we predicted ${pct(wb.avg_probability)}`],
              ["Average week", `${wb.avg_won_per_week.toFixed(1)}/10`, "picks won"],
              ["All 10 won", `${wb.perfect_weeks}/${wb.weeks}`, `${pct(wb.perfect_weeks / wb.weeks)} of weeks`],
              ["Picks", wb.n.toLocaleString("en-GB"), "mostly double chance"],
            ].map(([label, value, note]) => (
              <div key={label} className="rounded-xl border border-border p-3">
                <div className="text-xs text-text-3">{label}</div>
                <div className="mt-1 text-xl font-extrabold tabular">{value}</div>
                <div className="text-xs text-text-3">{note}</div>
              </div>
            ))}
          </div>
          <h3 className="mt-5 text-sm font-semibold">How many of the 10 won each week</h3>
          <div className="mt-2 space-y-1.5">
            {Object.entries(wb.won_distribution)
              .sort((a, b) => Number(b[0]) - Number(a[0]))
              .map(([won, count]) => (
                <div key={won} className="flex items-center gap-3 text-sm tabular">
                  <span className="w-12 shrink-0 text-text-2">{won}/10</span>
                  <span className="h-3 flex-1 rounded-full bg-surface-2">
                    <span
                      className="block h-3 rounded-full bg-win"
                      style={{ width: `${(count / Math.max(...Object.values(wb.won_distribution))) * 100}%` }}
                    />
                  </span>
                  <span className="w-20 shrink-0 text-right text-text-2">
                    {count} week{count === 1 ? "" : "s"}
                  </span>
                </div>
              ))}
          </div>
          <p className="mt-4 text-xs text-text-3">
            These are short prices (about 1.05–1.15), and bookmakers build their margin into them, so a high win rate
            doesn&apos;t mean profit. See the{" "}
            <Link href="/track-record" className="font-semibold text-accent hover:underline">
              track record
            </Link>
            .
          </p>
        </section>
      ) : null}
    </div>
  );
}
