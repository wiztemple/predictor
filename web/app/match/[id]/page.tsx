import type { Metadata } from "next";
import { AdSlot } from "@/components/AdSlot";
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
import { getBacktest, getCornersBacktest } from "@/lib/trackRecord";

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
    <div className="rounded-xl border border-border bg-surface p-3">
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold">{title}</h3>
        {note ? <span className="text-[11px] text-text-3">{note}</span> : null}
      </div>
      <div
        className={`grid gap-1.5 ${
          options.length === 2 ? "grid-cols-2" : options.length === 5 ? "grid-cols-5" : "grid-cols-3"
        }`}
      >
        {options.map((o) => (
          <OutcomeCell key={o.label} label={o.label} p={o.p} best={o.label === best} />
        ))}
      </div>
    </div>
  );
}

function PickCard({ market, pick, p }: { market: string; pick: string; p: number }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-3">
      <div className="text-xs font-medium text-text-3">{market}</div>
      <div className="mt-0.5 truncate font-bold">{pick}</div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="tabular">
          <span className="text-xl font-extrabold sm:text-2xl">{pct(p)}</span>
          <span className="ml-1.5 text-xs text-text-3">@{fairOdds(p)}</span>
        </div>
        <span className="hidden sm:inline">
          <ConfidenceBadge p={p} />
        </span>
      </div>
      <ConfidenceBar p={p} className="mt-2" />
    </div>
  );
}

const best = (opts: { pick: string; p: number }[]) => opts.reduce((a, b) => (b.p > a.p ? b : a));

export default async function MatchPage({ params }: PageProps<"/match/[id]">) {
  const [m, bt, cbt] = await Promise.all([getMatch((await params).id), getBacktest(), getCornersBacktest()]);
  if (!m) notFound();
  const x = m.extras;
  const mk = x.markets;
  // markets whose backtest beat the league average by less than 0.002 log loss: flag, don't oversell
  const noSkill = new Set(
    Object.entries(bt?.extra_markets ?? {})
      .filter(([, v]) => v.model - v.baseline > -0.002)
      .map(([k]) => k),
  );
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
        <div className="mt-3 overflow-hidden rounded-3xl border border-border bg-surface p-5 text-text sm:p-7">
          <p className="text-xs font-semibold tracking-widest text-text-3 uppercase">
            {formatDay(m.kickoff)} · {m.kickoff_tbc ? "time TBC" : `${formatTime(m.kickoff)} ${TIME_ZONE_LABEL}`}
          </p>
          <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
            <div className="flex min-w-0 flex-col items-center gap-2 text-center">
              <TeamBadge name={m.home} size="lg" />
              <div className="text-lg leading-tight font-extrabold sm:text-2xl">{m.home}</div>
              <span className="text-xs text-text-3">Home · {pct(h)}</span>
            </div>
            <div className="text-center">
              {top ? (
                <>
                  <div className="text-[11px] font-semibold tracking-wide text-text-3 uppercase">Likely score</div>
                  <div className="text-4xl font-black tabular sm:text-5xl">
                    {top.home}-{top.away}
                  </div>
                  <div className="text-[11px] text-text-3">{pct(top.p)} chance</div>
                </>
              ) : (
                <div className="text-2xl font-black">v</div>
              )}
            </div>
            <div className="flex min-w-0 flex-col items-center gap-2 text-center">
              <TeamBadge name={m.away} size="lg" />
              <div className="text-lg leading-tight font-extrabold sm:text-2xl">{m.away}</div>
              <span className="text-xs text-text-3">Away · {pct(a)}</span>
            </div>
          </div>
          <div className="mt-4 text-center text-xs text-text-3">Draw · {pct(d)}</div>
        </div>
      </div>

      {/* picks */}
      <section>
        <h2 className="mb-3 text-xl font-extrabold">
          <span className="text-accent">Our picks</span>
        </h2>
        <div className="grid grid-cols-2 gap-2 sm:gap-3 lg:grid-cols-4">
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
          {/* 10-minute market hidden for now:
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
          */}
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

      <AdSlot id="match-mid" />

      {mk ? (
        <section className="space-y-6">
          {(
            [
              {
                title: "Half-time",
                items: [
                  ["Half-time result", "ht_result", { "1": "1", X: "X", "2": "2" }],
                  ["Half-time / full-time", "htft", null],
                  ["1st half over/under 0.5", "ht_ou0_5", { over: "Over", under: "Under" }],
                  ["1st half over/under 1.5", "ht_ou1_5", { over: "Over", under: "Under" }],
                  ["Highest-scoring half", "highest_half", { "1st": "1st", "2nd": "2nd", equal: "Equal" }],
                ],
              },
              {
                title: "Result & goals",
                items: [
                  ["Result & both teams score", "result_btts", null],
                  ["Result & over/under 2.5", "result_ou25", null],
                  ["Double chance & over/under 2.5", "dc_ou25", null],
                  ["Draw no bet", "dnb", { "1": `1 (${m.home})`, "2": `2 (${m.away})` }],
                ],
              },
              {
                title: "Team goals",
                items: [
                  [`${m.home} over/under 0.5`, "home_ou0_5", { over: "Over", under: "Under" }],
                  [`${m.home} over/under 1.5`, "home_ou1_5", { over: "Over", under: "Under" }],
                  [`${m.away} over/under 0.5`, "away_ou0_5", { over: "Over", under: "Under" }],
                  [`${m.away} over/under 1.5`, "away_ou1_5", { over: "Over", under: "Under" }],
                ],
              },
              {
                title: "Total goals",
                items: [
                  ["Exact total goals", "exact_goals", null],
                  ["Odd / even goals", "odd_even", { odd: "Odd", even: "Even" }],
                ],
              },
            ] as { title: string; items: [string, string, Record<string, string> | null][] }[]
          ).map((group) => (
            <div key={group.title}>
              <h3 className="mb-2 text-base font-bold">{group.title}</h3>
              <div className="grid items-start gap-3 md:grid-cols-2">
                {group.items.map(([title, key, labels]) =>
                  mk[key] ? (
                    <Market
                      key={key}
                      title={title}
                      note={noSkill.has(key) ? "No better than league average" : undefined}
                      options={Object.entries(mk[key]).map(([o, p]) => ({ label: labels?.[o] ?? o, p }))}
                    />
                  ) : null,
                )}
                {group.title === "Team goals" ? (
                  <>
                    <Market
                      title="Clean sheet"
                      options={[
                        { label: `${m.home} yes`, p: mk.clean_sheet.home },
                        { label: `${m.away} yes`, p: mk.clean_sheet.away },
                      ]}
                    />
                    <Market
                      title="Win to nil"
                      options={[
                        { label: `${m.home} yes`, p: mk.win_to_nil.home },
                        { label: `${m.away} yes`, p: mk.win_to_nil.away },
                      ]}
                    />
                  </>
                ) : null}
              </div>
            </div>
          ))}
          <p className="text-xs text-text-3">
            Every market here comes from one scoreline model that matches the result and goals numbers above, so they
            all agree. Each was backtested over three seasons; see the{" "}
            <Link href="/track-record" className="text-accent font-semibold hover:underline">
              track record
            </Link>
            .
          </p>
        </section>
      ) : null}

      {/* corners */}
      {x.corners ? (
        <section>
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h2 className="text-lg font-semibold">Corners</h2>
            <p className="text-sm text-text-2">
              Expected:{" "}
              <span className="font-semibold text-text tabular">
                {m.home} {x.corners.expected.home.toFixed(1)} – {x.corners.expected.away.toFixed(1)} {m.away}
              </span>{" "}
              · total <span className="font-semibold text-text tabular">{x.corners.expected.total.toFixed(1)}</span>
            </p>
          </div>
          <div className="grid items-start gap-3 md:grid-cols-2">
            {Object.entries(x.corners.over).map(([line, p]) => (
              <Market
                key={line}
                title={`Total corners over/under ${line}`}
                options={[
                  { label: "Over", p },
                  { label: "Under", p: 1 - p },
                ]}
              />
            ))}
          </div>
          <p className="mt-3 text-xs text-text-3">
            {cbt
              ? `Tested on ${cbt.n_matches.toLocaleString("en-GB")} past matches: more accurate than each league's average on every line, and well calibrated. `
              : ""}
            Our data has no bookmaker corner odds, so we can&apos;t say how it compares with the bookies.{" "}
            <Link href="/track-record#corners" className="font-semibold text-accent hover:underline">
              Track record
            </Link>
          </p>
        </section>
      ) : null}

      {/* score grid */}
      {x.score_grid ? (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Every scoreline</h2>
          <ScoreGrid cells={x.score_grid.cells} other={x.score_grid.other} home={m.home} away={m.away} />
        </section>
      ) : null}

      {/* details */}
      <details className="rounded-xl border border-border bg-surface p-4 text-sm">
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
