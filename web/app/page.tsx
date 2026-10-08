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
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Predictions</h1>
          <p className="mt-1 text-sm text-text-2">
            {matches.length} matches · {new Set(matches.map((m) => m.league)).size} leagues · times {TIME_ZONE_LABEL}
          </p>
        </div>
        <p className="max-w-md text-xs text-text-3">
          <strong className="font-semibold text-text-2">%</strong> is our chance of it happening.{" "}
          <strong className="font-semibold text-text-2">@odds</strong> are the fair odds for that chance (1 ÷ chance).
          Highlighted = most likely.
        </p>
      </div>
      <div className="mt-4">
        <PicksPanel picks={panelPicks(doc.predictions, perDay)} record={recordLine(live, pbt)} />
      </div>
      <h2 className="mt-10 text-xl font-bold tracking-tight">All matches</h2>
      <div className="mt-2">
        <MatchBoard matches={matches} leagues={leagues} track={track} />
      </div>
    </div>
  );
}
