import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { AsianHandicap } from "@/components/AsianHandicap";
import { OutcomeCell } from "@/components/OutcomeCell";
import { ScoreGrid } from "@/components/ScoreGrid";
import { TIME_ZONE_LABEL, formatDay, formatTime, modelLabel, pct } from "@/lib/format";
import { fairOdds } from "@/lib/markets";
import { ConfidenceBadge, ConfidenceBar, LeagueDot, TeamBadge } from "@/components/ui";
import { leagueColor } from "@/lib/leagues";
import { getMatch, getPredictions } from "@/lib/predictions";

export async function generateStaticParams() {
  const doc = await getPredictions();
  return doc.predictions.map((p) => ({ id: p.id }));
}

export async function generateMetadata({ params }: PageProps<"/match/[id]">): Promise<Metadata> {
  const m = await getMatch((await params).id);
  return { title: m ? `${m.home} vs ${m.away}` : "Match" };
}

type Opt = { label: string; p: number };

function Market({ title, options, note }: { title: string; options: Opt[]; note?: string }) {
  if (!options.length) return null;
  const best = options.reduce((a, b) => (b.p > a.p ? b : a)).label;
  return (
    <div className="rounded-xl border border-border bg-surface p-3 shadow-sm">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">{title}</h3>
        {note ? <span className="text-[11px] text-text-3">{note}</span> : null}
      </div>
      <div className={`grid gap-1.5 ${options.length === 2 ? "grid-cols-2" : options.length === 3 ? "grid-cols-3" : "grid-cols-5"}`}>
        {options.map((o) => (
          <OutcomeCell key={o.label} label={o.label} p={o.p} best={o.label === best} />
        ))}
      </div>
    </div>
  );
}

function PickCard({ market, pick, p }: { market: string; pick: string; p: number }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-3 shadow-sm">
      <div className="text-xs font-medium text-text-3">{market}</div>
      <div className="mt-0.5 truncate font-bold">{pick}</div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="tabular">
          <span className="text-2xl font-extrabold">{pct(p)}</span>
          <span className="ml-1.5 text-xs text-text-3">fair @{fairOdds(p)}</span>
        </div>
        <ConfidenceBadge p={p} />
      </div>
      <ConfidenceBar p={p} className="mt-2" />
    </div>
  );
}

const best = (opts: { pick: string; p: number }[]) => opts.reduce((a, b) => (b.p > a.p ? b : a));

export default async function MatchPage({ params }: PageProps<"/match/[id]">) {
  const m = await getMatch((await params).id);
  if (!m) notFound();
  const x = m.extras;
  const { home: h, draw: d, away: a } = m.probabilities;
  const top = x.top_scorelines?.[0];

  const picks: { market: string; pick: string; p: number }[] = [
    { market: "Match result", ...best([{ pick: `${m.home} win`, p: h }, { pick: "Draw", p: d }, { pick: `${m.away} win`, p: a }]) },
  ];
  if (x.over_1_5 !== undefined) picks.push({ market: "Goals", ...best([{ pick: "Over 1.5", p: x.over_1_5 }, { pick: "Under 1.5", p: 1 - x.over_1_5 }]) });
  if (x.over_2_5 !== undefined) picks.push({ market: "Goals", ...best([{ pick: "Over 2.5", p: x.over_2_5 }, { pick: "Under 2.5", p: 1 - x.over_2_5 }]) });
  if (x.btts !== undefined) picks.push({ market: "Both teams to score", ...best([{ pick: "GG (yes)", p: x.btts }, { pick: "NG (no)", p: 1 - x.btts }]) });

  const ou = (p: number | undefined): Opt[] => (p === undefined ? [] : [{ label: "Over", p }, { label: "Under", p: 1 - p }]);

  return (
    <div className="space-y-8">
      {/* header */}
      <div>
        <Link href={`/league/${m.league}`} className="inline-flex items-center gap-2 text-sm text-accent font-semibold hover:underline">
          <LeagueDot color={leagueColor(m.league)} />← {m.league_name}
        </Link>
        <h1 className="sr-only">
          {m.home} v {m.away}
        </h1>
        <div className="bg-brand mt-3 overflow-hidden rounded-3xl p-5 text-white sm:p-7">
          <p className="text-xs font-semibold tracking-widest text-white/80 uppercase">
            {formatDay(m.kickoff)} · {m.kickoff_tbc ? "time TBC" : `${formatTime(m.kickoff)} ${TIME_ZONE_LABEL}`}
          </p>
          <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
            <div className="flex min-w-0 flex-col items-center gap-2 text-center">
              <TeamBadge name={m.home} size="lg" />
              <div className="text-lg leading-tight font-extrabold sm:text-2xl">{m.home}</div>
              <span className="text-xs text-white/75">Home · {pct(h)}</span>
            </div>
            <div className="text-center">
              {top ? (
                <>
                  <div className="text-[11px] font-semibold tracking-wide text-white/75 uppercase">Likely score</div>
                  <div className="text-4xl font-black tabular sm:text-5xl">
                    {top.home}-{top.away}
                  </div>
                  <div className="text-[11px] text-white/75">{pct(top.p)} chance</div>
                </>
              ) : (
                <div className="text-2xl font-black">v</div>
              )}
            </div>
            <div className="flex min-w-0 flex-col items-center gap-2 text-center">
              <TeamBadge name={m.away} size="lg" />
              <div className="text-lg leading-tight font-extrabold sm:text-2xl">{m.away}</div>
              <span className="text-xs text-white/75">Away · {pct(a)}</span>
            </div>
          </div>
          <div className="mt-4 text-center text-xs text-white/75">Draw · {pct(d)}</div>
        </div>
      </div>

      {/* picks */}
      <section>
        <h2 className="mb-3 text-xl font-extrabold">
          <span className="text-accent">Our picks</span>
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {picks.map((p) => (
            <PickCard key={p.pick} {...p} />
          ))}
        </div>
        <p className="mt-2 text-xs text-text-3">
          The most likely option in each market. Fair odds = 1 ÷ our chance. A bookmaker price above the fair odds
          only means our model rates it higher, and bookmakers have been more accurate than us over time.
        </p>
      </section>

      {/* markets */}
      <section>
        <h2 className="mb-3 text-lg font-semibold">All markets</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <Market title="Match result (1X2)" options={[{ label: "1", p: h }, { label: "X", p: d }, { label: "2", p: a }]} />
          <Market title="Double chance" options={[{ label: "1X", p: h + d }, { label: "12", p: h + a }, { label: "X2", p: d + a }]} />
          {x.ten_min ? (
            <Market
              title="Result after 10 minutes"
              note="Estimate · no track record"
              options={[
                { label: "1", p: x.ten_min.home },
                { label: "X", p: x.ten_min.draw },
                { label: "2", p: x.ten_min.away },
              ]}
            />
          ) : null}
          <Market title="Over/Under 1.5" options={ou(x.over_1_5)} />
          <Market title="Over/Under 2.5" options={ou(x.over_2_5)} />
          <Market title="Over/Under 3.5" options={ou(x.over_3_5)} />
          <Market
            title="Both teams to score"
            options={x.btts === undefined ? [] : [{ label: "GG", p: x.btts }, { label: "NG", p: 1 - x.btts }]}
          />
        </div>
        {x.margin ? (
          <div className="mt-3">
            <AsianHandicap margin={x.margin} home={m.home} away={m.away} />
          </div>
        ) : null}
        {x.top_scorelines?.length ? (
          <div className="mt-3">
            <Market
              title="Correct score (top 5)"
              note="Exact scores rarely land; even the top one is a long shot"
              options={x.top_scorelines.map((s) => ({ label: `${s.home}-${s.away}`, p: s.p }))}
            />
          </div>
        ) : null}
        {x.expected_goals ? (
          <p className="mt-3 text-sm text-text-2">
            Expected goals:{" "}
            <span className="font-semibold text-text tabular">
              {m.home} {x.expected_goals.home.toFixed(2)} – {x.expected_goals.away.toFixed(2)} {m.away}
            </span>
          </p>
        ) : null}
      </section>

      {/* score grid */}
      {x.score_grid ? (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Every scoreline</h2>
          <ScoreGrid cells={x.score_grid.cells} other={x.score_grid.other} home={m.home} away={m.away} />
        </section>
      ) : null}

      {/* details */}
      <details className="rounded-xl border border-border bg-surface p-4 text-sm shadow-sm">
        <summary className="cursor-pointer font-medium">How we got these numbers</summary>
        <div className="mt-3 space-y-3 text-text-2">
          <p>
            Result chances blend two models built from past results: Elo ratings and a Dixon-Coles goals model. Goals
            and score chances come from Dixon-Coles; over/under and GG are adjusted using past seasons so they match how
            often things really happened.
          </p>
          <table className="w-full max-w-md tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal">Model</th>
                <th className="py-1 text-right font-normal">1</th>
                <th className="py-1 text-right font-normal">X</th>
                <th className="py-1 text-right font-normal">2</th>
              </tr>
            </thead>
            <tbody>
              {[{ ...m.model, probabilities: m.probabilities }, ...m.other_models].map((row) => (
                <tr key={row.name} className="border-t border-border">
                  <td className="py-1.5">{modelLabel(row.name)}</td>
                  <td className="py-1.5 text-right">{pct(row.probabilities.home)}</td>
                  <td className="py-1.5 text-right">{pct(row.probabilities.draw)}</td>
                  <td className="py-1.5 text-right">{pct(row.probabilities.away)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-text-3">
            Model {modelLabel(m.model.name)} v{m.model.version} · generated {new Date(m.generated_at).toUTCString()} ·{" "}
            <Link href="/track-record" className="text-accent font-semibold hover:underline">
              track record
            </Link>
          </p>
        </div>
      </details>
    </div>
  );
}
