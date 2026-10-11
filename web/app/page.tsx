import { MatchBoard } from "@/components/MatchBoard";
import { AdSlot } from "@/components/AdSlot";
import { PicksPanel } from "@/components/PicksPanel";
import { panelPicks, recordLine } from "@/lib/panel";
import Link from "next/link";
import { getPicksBacktest, getPicksSummary, getWeekly } from "@/lib/picksRecord";
import { toBoardMatch, trackTables } from "@/lib/board";
import { TIME_ZONE_LABEL } from "@/lib/format";
import { leagueOrder } from "@/lib/leagues";
import { getPredictions } from "@/lib/predictions";
import { getBacktest, getCornersBacktest } from "@/lib/trackRecord";

export default async function Home() {
  const [doc, bt, live, pbt, weekly, cbt] = await Promise.all([
    getPredictions(),
    getBacktest(),
    getPicksSummary(),
    getPicksBacktest(),
    getWeekly(),
    getCornersBacktest(),
  ]);
  const weeklyLists = Object.entries(weekly?.lists ?? {});
  const perDay = pbt?.rule.per_day ?? live?.per_day ?? 10;

  const matches = doc.predictions.map(toBoardMatch);
  const leagues = doc.leagues
    .map(({ code, name }) => ({ code, name }))
    .sort((a, b) => leagueOrder(a.code) - leagueOrder(b.code));
  const track = trackTables(bt, cbt);

  return (
    <div>
      {/* slim header: title + key numbers on one line, how-to-read underneath */}
      <section className="flex flex-wrap items-end justify-between gap-x-4 gap-y-2">
        <div>
          <p className="text-[11px] font-semibold tracking-widest text-text-3 uppercase">Football predictions</p>
          <h1 className="text-xl font-extrabold tracking-tight sm:text-2xl">This week&apos;s matches, by the numbers</h1>
        </div>
        <div className="flex flex-wrap gap-1.5 text-xs">
          {[
            `${matches.length} matches`,
            `${new Set(matches.map((m) => m.league)).size} leagues`,
            ...(pbt?.top_per_day.hit_rate !== undefined
              ? [`${Math.round(pbt.top_per_day.hit_rate * 100)}% of top picks won in testing`]
              : []),
          ].map((t) => (
            <span key={t} className="rounded-full px-2.5 py-0.5 font-semibold text-text-2 ring-1 ring-border">
              {t}
            </span>
          ))}
        </div>
      </section>
      <p className="mt-1.5 text-xs text-text-3">
        <strong className="font-semibold text-text-2">%</strong> is our chance ·{" "}
        <strong className="font-semibold text-text-2">@odds</strong> are the fair odds for it · the green box is the most
        likely option · times are {TIME_ZONE_LABEL}
      </p>

      <div className="mt-4">
        <PicksPanel picks={panelPicks(doc.predictions, perDay)} record={recordLine(live, pbt)} limit={5} />
      </div>
      {weeklyLists.length ? (
        <section className="mt-3 flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-surface px-3 py-2.5">
          <h2 className="mr-1 text-sm font-bold">This week&apos;s top 10s</h2>
          {weeklyLists.map(([key, l]) => {
            const w = l.weeks[0];
            return (
              <Link
                key={key}
                href={key === "safe" ? "/weekly" : `/weekly/${key}`}
                className="rounded-full border border-border px-2.5 py-0.5 text-xs transition hover:border-accent hover:text-accent"
              >
                <span className="font-semibold">{l.label}</span>
                {w ? (
                  <span className="ml-1 text-text-3 tabular">
                    {w.won + w.half_won}/{w.picks.length - w.pending - w.void}
                  </span>
                ) : null}
              </Link>
            );
          })}
          <Link href="/weekly" className="ml-auto text-xs font-semibold text-accent hover:underline">
            All lists →
          </Link>
        </section>
      ) : null}
      <AdSlot id="home-mid" className="mt-5" />
      <h2 className="mt-6 text-lg font-extrabold tracking-tight">All matches</h2>
      <div className="mt-2">
        <MatchBoard matches={matches} leagues={leagues} track={track} />
      </div>
    </div>
  );
}
