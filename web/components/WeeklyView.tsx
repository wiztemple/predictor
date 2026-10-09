import Link from "next/link";
import { Integrity } from "@/components/Integrity";
import { TeamBadge } from "@/components/ui";
import { formatShortDay, formatTime, pct } from "@/lib/format";
import { fairOdds } from "@/lib/markets";
import { type PickState, type WeeklyBacktest, type WeeklyList, type WeeklyListSummary, MARKET_NAMES } from "@/lib/picksRecord";

const STATE: Record<PickState, { text: string; pill: string; seg: string }> = {
  pending: { text: "To play", pill: "bg-surface text-text-2 ring-border", seg: "bg-border" },
  won: { text: "Won ✓", pill: "bg-surface text-win ring-win/40", seg: "bg-win" },
  half_won: { text: "½ won", pill: "bg-surface text-win ring-win/40", seg: "bg-win/60" },
  push: { text: "Push", pill: "bg-surface text-text-2 ring-border", seg: "bg-text-3/50" },
  half_lost: { text: "½ lost", pill: "bg-surface text-[#b42323] ring-[#d03b3b]/40", seg: "bg-[#d03b3b]/60" },
  lost: { text: "Lost ✗", pill: "bg-surface text-[#b42323] ring-[#d03b3b]/40", seg: "bg-[#d03b3b]" },
  void: { text: "Void", pill: "bg-surface text-text-3 ring-border", seg: "bg-text-3/30" },
};

const weekLabel = (w: WeeklyList) => `${formatShortDay(w.week_start)} – ${formatShortDay(w.week_end)}`;
const signedPct = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(v * 100).toFixed(1)}%`;

function tally(w: WeeklyList) {
  const parts = [`${w.won} won`];
  if (w.half_won) parts.push(`${w.half_won} ½ won`);
  if (w.push) parts.push(`${w.push} push`);
  if (w.half_lost) parts.push(`${w.half_lost} ½ lost`);
  parts.push(`${w.lost} lost`);
  if (w.void) parts.push(`${w.void} void`);
  if (w.pending) parts.push(`${w.pending} to play`);
  return parts.join(" · ");
}

function WeekCard({ w, current }: { w: WeeklyList; current: boolean }) {
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 sm:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="text-lg font-bold">
          {current ? "This week" : "Week"} · {weekLabel(w)}
        </h2>
        <p className="text-sm font-semibold tabular">{tally(w)}</p>
      </div>
      <div className="mt-3 flex gap-1" aria-hidden>
        {w.picks.map((p) => (
          <span key={p.rank} className={`h-2 flex-1 rounded-full ${STATE[p.state].seg}`} />
        ))}
      </div>
      {w.pending === w.picks.length ? (
        <p className="mt-2 text-xs text-text-3">
          Locked {formatShortDay(w.locked_at)} {formatTime(w.locked_at)}. Results appear as matches finish.
        </p>
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
                  {formatShortDay(p.kickoff)} · {p.market === "ah" ? "Asian handicap" : (MARKET_NAMES[p.market] ?? p.market)}
                </span>
              </span>
            </span>
            <span className="shrink-0 text-right tabular">
              <span className="block font-bold">@{fairOdds(p.probability)}</span>
              <span className="block text-[11px] text-text-3">{pct(p.probability)}</span>
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

function Backtest({ b }: { b: WeeklyBacktest }) {
  const maxCount = Math.max(...Object.values(b.won_distribution));
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 sm:p-5">
      <h2 className="text-lg font-bold">How this list did in testing</h2>
      <p className="mt-1 max-w-2xl text-sm text-text-2">
        The same rule replayed over {b.weeks} weeks (2023-24 to now), using only what our model knew at the start of
        each week.
      </p>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 sm:gap-3">
        {[
          ["Average odds", `@${b.avg_fair_odds.toFixed(2)}`, "our fair odds"],
          ["Picks won", pct(b.hit_rate), `we predicted ${pct(b.avg_probability)}`],
          ["Average week", `${b.avg_won_per_week.toFixed(1)}/10`, "won"],
          ["All 10 won", `${b.perfect_weeks}/${b.weeks}`, "weeks"],
        ].map(([label, value, note]) => (
          <div key={label} className="rounded-xl border border-border p-3">
            <div className="text-xs text-text-3">{label}</div>
            <div className="mt-1 text-xl font-extrabold tabular">{value}</div>
            <div className="text-xs text-text-3">{note}</div>
          </div>
        ))}
      </div>
      {b.calibration_gap < -0.03 ? (
        <p className="mt-3 rounded-xl border border-notice-border bg-notice-bg p-3 text-sm text-notice-text">
          <strong>Read with care:</strong> these picks won {pct(b.hit_rate)} against the {pct(b.avg_probability)} we
          predicted. Picking the likeliest option in a price range tends to pick where our model is most optimistic.
        </p>
      ) : null}
      <h3 className="mt-5 text-sm font-semibold">How many of the 10 won each week</h3>
      <div className="mt-2 space-y-1.5">
        {Object.entries(b.won_distribution)
          .sort((x, y) => Number(y[0]) - Number(x[0]))
          .map(([won, count]) => (
            <div key={won} className="flex items-center gap-3 text-sm tabular">
              <span className="w-12 shrink-0 text-text-2">{won}/10</span>
              <span className="h-3 flex-1 rounded-full bg-border">
                <span className="block h-3 rounded-full bg-win" style={{ width: `${(count / maxCount) * 100}%` }} />
              </span>
              <span className="w-20 shrink-0 text-right text-text-2">
                {count} week{count === 1 ? "" : "s"}
              </span>
            </div>
          ))}
      </div>
      {b.priced ? (
        <p className="mt-4 text-sm text-text-2">
          At bookmakers&apos; closing odds (where we have them: {b.priced.n.toLocaleString("en-GB")} picks, average @
          {b.priced.avg_odds.toFixed(2)}), backing every pick returned{" "}
          <strong className="text-text">{signedPct(b.priced.roi)}</strong> per bet (95% range {signedPct(b.priced.roi_ci[0])}{" "}
          to {signedPct(b.priced.roi_ci[1])}).{" "}
          {b.priced.roi_ci[0] > 0
            ? "That suggests a real edge, though past results don't guarantee future ones."
            : "That range includes zero, so it isn't evidence of an edge either way."}
        </p>
      ) : (
        <p className="mt-4 text-xs text-text-3">
          Our data has no bookmaker odds for most of these picks, so we can&apos;t show a profit figure. Bookmakers
          build a margin into their prices, so a good hit rate alone doesn&apos;t mean profit.
        </p>
      )}
    </section>
  );
}

export function WeeklyView({
  lists,
  active,
  data,
  backtest,
}: {
  lists: { key: string; label: string }[];
  active: string;
  data: WeeklyListSummary | undefined;
  backtest: WeeklyBacktest | undefined;
}) {
  const [current, ...past] = data?.weeks ?? [];
  const rec = data?.record;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Weekly top 10s</h1>
        <p className="mt-1 max-w-2xl text-sm text-text-2">
          Eight lists of 10, from safe short prices to long shots. Each covers Tuesday to Monday. It&apos;s picked at
          the start of the week from matches not yet played, saved to our database, and never changed after that.
          Odds shown are our fair odds; bookmakers&apos; prices will be a little lower.
        </p>
      </div>

      <nav aria-label="Lists" className="-mx-4 flex gap-2 overflow-x-auto px-4">
        {lists.map((l) => (
          <Link
            key={l.key}
            href={l.key === "safe" ? "/weekly" : `/weekly/${l.key}`}
            aria-current={l.key === active ? "page" : undefined}
            className={`shrink-0 rounded-full border px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors ${
              l.key === active ? "tab-active" : "border-border text-text-2 hover:border-accent hover:text-accent"
            }`}
          >
            {l.label}
          </Link>
        ))}
      </nav>

      {data ? (
        <div>
          <h2 className="text-xl font-bold">{data.label}</h2>
          <p className="mt-0.5 text-sm text-text-2">
            {data.description}
            {backtest ? ` In testing, about ${backtest.avg_won_per_week.toFixed(1)} of the 10 won in an average week.` : ""}
          </p>
        </div>
      ) : null}

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
            {rec.weeks} finished week{rec.weeks === 1 ? "" : "s"} · {rec.won + rec.half_won / 2}/{rec.picks} won
            {rec.picks ? ` (${pct((rec.won + rec.half_won / 2) / rec.picks)})` : ""} · all 10 won in {rec.perfect_weeks}{" "}
            week{rec.perfect_weeks === 1 ? "" : "s"}
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
                <span className="text-sm tabular">{tally(w)}</span>
              </summary>
              <div className="mt-3">
                <WeekCard w={w} current={false} />
              </div>
            </details>
          ))}
        </section>
      ) : null}

      {backtest ? <Backtest b={backtest} /> : null}

      <Integrity />
    </div>
  );
}
