import { MatchBoard } from "@/components/MatchBoard";
import { PicksPanel } from "@/components/PicksPanel";
import { panelPicks, recordLine } from "@/lib/panel";
import { getPicksBacktest, getPicksSummary } from "@/lib/picksRecord";
import { toBoardMatch, trackTables } from "@/lib/board";
import { TIME_ZONE_LABEL } from "@/lib/format";
import { leagueOrder } from "@/lib/leagues";
import { getPredictions } from "@/lib/predictions";
import { getBacktest } from "@/lib/trackRecord";

export default async function Home() {
  const [doc, bt, live, pbt] = await Promise.all([getPredictions(), getBacktest(), getPicksSummary(), getPicksBacktest()]);
  const perDay = pbt?.rule.per_day ?? live?.per_day ?? 10;

  const matches = doc.predictions.map(toBoardMatch);
  const leagues = doc.leagues
    .map(({ code, name }) => ({ code, name }))
    .sort((a, b) => leagueOrder(a.code) - leagueOrder(b.code));
  const track = trackTables(bt);

  return (
    <div>
      <section className="rounded-3xl border border-border bg-surface px-5 py-6 text-text sm:px-8 sm:py-8">
        <div>
          <p className="text-xs font-semibold tracking-widest text-text-3 uppercase">Football predictions</p>
          <h1 className="mt-1 text-3xl font-extrabold tracking-tight sm:text-4xl">This week&apos;s matches, by the numbers</h1>
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            {[
              `${matches.length} matches`,
              `${new Set(matches.map((m) => m.league)).size} leagues`,
              ...(pbt?.top_per_day.hit_rate !== undefined
                ? [`${Math.round(pbt.top_per_day.hit_rate * 100)}% of our top picks won in testing`]
                : []),
            ].map((t) => (
              <span key={t} className="rounded-full bg-surface-2 px-3 py-1 font-semibold text-text-2 ring-1 ring-border">
                {t}
              </span>
            ))}
          </div>
          <p className="mt-4 max-w-xl text-sm text-text-2">
            <strong className="font-bold text-text">%</strong> is our chance of it happening.{" "}
            <strong className="font-bold text-text">@odds</strong> are the fair odds for that chance. The green cell is
            the most likely option. Times are {TIME_ZONE_LABEL}.
          </p>
        </div>
      </section>
      <div className="mt-6">
        <PicksPanel picks={panelPicks(doc.predictions, perDay)} record={recordLine(live, pbt)} />
      </div>
      <h2 className="mt-10 text-2xl font-extrabold tracking-tight">All matches</h2>
      <div className="mt-2">
        <MatchBoard matches={matches} leagues={leagues} track={track} />
      </div>
    </div>
  );
}
