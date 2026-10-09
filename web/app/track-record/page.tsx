import type { Metadata } from "next";
import { ReliabilityChart } from "@/components/ReliabilityChart";
import { pct } from "@/lib/format";
import { getPredictions } from "@/lib/predictions";
import { LiveRecord } from "@/components/LiveRecord";
import {
  getBacktest,
  getCornersBacktest,
  getLiveSummary,
  type BacktestSummary,
  type CornersBacktest,
} from "@/lib/trackRecord";

export const metadata: Metadata = { title: "Track record" };

const GOALS_ROWS = [
  ["over_1_5", "Over/under 1.5"],
  ["over_2_5", "Over/under 2.5"],
  ["over_3_5", "Over/under 3.5"],
  ["btts", "Both teams score"],
] as const;

const signed = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(3)}`;

function Stat({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="rounded-lg border border-border p-4">
      <div className="text-sm text-text-2">{label}</div>
      <div className="mt-1 text-2xl font-semibold tabular">{value}</div>
      {note ? <div className="mt-1 text-xs text-text-3">{note}</div> : null}
    </div>
  );
}

function CornersRecord({ c }: { c: CornersBacktest }) {
  const ci = c.count_log_loss.gain_ci;
  return (
    <section id="corners" className="scroll-mt-4">
      <h2 className="mb-1 text-lg font-semibold">Corners</h2>
      <p className="mb-3 max-w-2xl text-sm text-text-2">
        Total corners, tested week by week on {c.n_matches.toLocaleString("en-GB")} matches in {c.test_seasons[0]} to{" "}
        {c.test_seasons[c.test_seasons.length - 1]}, with settings chosen on earlier seasons only. On average matches had{" "}
        {c.mean_total.toFixed(2)} corners and we predicted {c.mean_predicted.toFixed(2)}. Our data has no bookmaker
        corner odds, so the comparison is with each league&apos;s average, not with the bookies.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full max-w-3xl text-sm tabular">
          <thead>
            <tr className="text-left text-text-3">
              <th className="py-1 font-normal">Line</th>
              <th className="py-1 text-right font-normal">Went over</th>
              <th className="py-1 text-right font-normal">League average</th>
              <th className="py-1 text-right font-normal">Ours</th>
              <th className="py-1 text-right font-normal">Our 65%+ calls</th>
            </tr>
          </thead>
          <tbody>
            {Object.values(c.lines).map((l) => {
              const calls = l.thresholds
                .filter((t) => t.min_p === 0.65)
                .sort((a, b) => b.n - a.n)[0];
              return (
                <tr key={l.line} className="border-t border-border">
                  <td className="py-1.5">Over/under {l.line}</td>
                  <td className="py-1.5 text-right">{pct(l.base_rate)}</td>
                  <td className="py-1.5 text-right">{l.baseline.log_loss.toFixed(4)}</td>
                  <td className="py-1.5 text-right">{l.model.log_loss.toFixed(4)}</td>
                  <td className="py-1.5 text-right text-text-2">
                    {calls ? (
                      <>
                        {calls.direction === "over" ? "Over" : "Under"}: won {pct(calls.hit_rate)}{" "}
                        <span className="text-text-3">
                          (said {pct(calls.mean_pred)}, {calls.n.toLocaleString("en-GB")})
                        </span>
                      </>
                    ) : (
                      "–"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-text-3">
        Log loss, lower is better. Across all corner counts we beat the league average by{" "}
        {c.count_log_loss.gain.toFixed(4)} (95% interval {ci[0].toFixed(4)} to {ci[1].toFixed(4)}): a real but small
        edge, because most of what decides corners is luck on the day.
      </p>
    </section>
  );
}

function Backtest({ bt, leagueName }: { bt: BacktestSummary; leagueName: Map<string, string> }) {
  const prod = bt.production_model;
  const overall = bt.rows.filter((r) => r.league === "ALL");
  const ours = overall.find((r) => r.model === prod)!;
  const book = overall.find((r) => r.model === "bookmaker")!;
  const gap = bt.gap_to_bookmaker[prod];
  const leagues = [...new Set(bt.rows.map((r) => r.league))].filter((l) => l !== "ALL").sort();
  const row = (model: string, league: string) => bt.rows.find((r) => r.model === model && r.league === league)!;
  const beatsBook = gap.ci_high < 0;
  const lagsBook = gap.ci_low > 0;
  const seasons = `${bt.test_seasons[0]} to ${bt.test_seasons[bt.test_seasons.length - 1]}`;

  return (
    <>
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Backtest: {seasons}</h2>
        <p className="max-w-2xl text-text-2">
          {lagsBook
            ? `Over ${bt.n_matches.toLocaleString("en-GB")} matches, our model was less accurate than the bookmaker's closing odds. That's normal for a model built only on past results, because closing odds also reflect team news, injuries and lineups.`
            : beatsBook
              ? `Over ${bt.n_matches.toLocaleString("en-GB")} matches, our model was more accurate than the bookmaker's closing odds.`
              : `Over ${bt.n_matches.toLocaleString("en-GB")} matches, we can't tell our model and the bookmaker's closing odds apart.`}
        </p>
        <div className="grid gap-3 sm:grid-cols-3">
          <Stat label={`Log loss: ${bt.labels[prod]}`} value={ours.log_loss.toFixed(3)} note="Lower is better" />
          <Stat label="Log loss: bookmaker" value={book.log_loss.toFixed(3)} note="Closing odds, margin removed" />
          <Stat
            label="Gap to bookmaker"
            value={signed(gap.mean)}
            note={`95% interval ${signed(gap.ci_low)} to ${signed(gap.ci_high)}. Positive means the bookmaker did better.`}
          />
        </div>
        <p className="text-sm text-text-2">
          The most likely outcome happened in {pct(ours.accuracy)} of matches for our model and {pct(book.accuracy)}{" "}
          for the bookmaker.
        </p>
      </section>

      <section>
        <h3 className="mb-3 font-semibold">Every model tested</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal">Model</th>
                <th className="py-1 text-right font-normal">Log loss</th>
                <th className="py-1 text-right font-normal">Brier</th>
                <th className="py-1 text-right font-normal">Accuracy</th>
                <th className="py-1 text-right font-normal">Gap to bookmaker (95% interval)</th>
              </tr>
            </thead>
            <tbody>
              {overall.toSorted((a, b) => a.log_loss - b.log_loss).map((r) => {
                const g = bt.gap_to_bookmaker[r.model];
                return (
                  <tr key={r.model} className="border-t border-border">
                    <td className="py-1.5">
                      {r.label}
                      {r.model === prod ? <span className="ml-1.5 text-xs text-text-3">(used on this site)</span> : null}
                    </td>
                    <td className="py-1.5 text-right">{r.log_loss.toFixed(4)}</td>
                    <td className="py-1.5 text-right">{r.brier.toFixed(4)}</td>
                    <td className="py-1.5 text-right">{pct(r.accuracy)}</td>
                    <td className="py-1.5 text-right text-text-2">
                      {g ? `${signed(g.mean)} (${signed(g.ci_low)} to ${signed(g.ci_high)})` : "–"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-text-3">
          &ldquo;With odds&rdquo; uses the bookmaker&apos;s own closing odds as an input, so it can&apos;t be used before
          those odds exist. It&apos;s shown to check whether our models add anything to the market. They don&apos;t.
        </p>
      </section>

      <section>
        <h3 className="mb-3 font-semibold">By league</h3>
        <div className="overflow-x-auto">
          <table className="w-full max-w-xl text-sm tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal">League</th>
                <th className="py-1 text-right font-normal">Matches</th>
                <th className="py-1 text-right font-normal">Our log loss</th>
                <th className="py-1 text-right font-normal">Bookmaker</th>
                <th className="py-1 text-right font-normal">Gap</th>
              </tr>
            </thead>
            <tbody>
              {leagues.map((lg) => {
                const a = row(prod, lg);
                const b = row("bookmaker", lg);
                return (
                  <tr key={lg} className="border-t border-border">
                    <td className="py-1.5">{leagueName.get(lg) ?? lg}</td>
                    <td className="py-1.5 text-right">{a.n.toLocaleString("en-GB")}</td>
                    <td className="py-1.5 text-right">{a.log_loss.toFixed(4)}</td>
                    <td className="py-1.5 text-right">{b.log_loss.toFixed(4)}</td>
                    <td className="py-1.5 text-right">{signed(a.log_loss - b.log_loss)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h3 className="mb-1 font-semibold">Calibration</h3>
        <p className="mb-4 max-w-2xl text-sm text-text-2">
          When our model says 40%, does it happen about 40% of the time? Points near the dashed line mean yes. Ours
          sit close to it, so the percentages can be read at face value. Being well calibrated isn&apos;t the same as
          being sharp, though: the bookmaker is both.
        </p>
        <ReliabilityChart bins={bt.reliability[prod]} />
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-text-2">Show as a table</summary>
          <table className="mt-2 w-full max-w-md tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal">Outcome</th>
                <th className="py-1 font-normal">Predicted</th>
                <th className="py-1 text-right font-normal">Happened</th>
                <th className="py-1 text-right font-normal">Matches</th>
              </tr>
            </thead>
            <tbody>
              {bt.reliability[prod].filter((b) => b.n >= 30).map((b) => (
                <tr key={`${b.outcome}-${b.bin_lo}`} className="border-t border-border">
                  <td className="py-1 capitalize">{b.outcome}</td>
                  <td className="py-1">{pct(b.mean_pred)}</td>
                  <td className="py-1 text-right">{pct(b.observed)}</td>
                  <td className="py-1 text-right">{b.n.toLocaleString("en-GB")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      </section>

      {bt.goals_markets ? (
        <section>
          <h3 className="mb-1 font-semibold">Goals markets</h3>
          <p className="mb-3 max-w-2xl text-sm text-text-2">
            Over/under and both-teams-to-score chances from the Dixon-Coles model, calibrated using earlier seasons
            only. &ldquo;League average&rdquo; just uses each league&apos;s past rate, with no model at all.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full max-w-3xl text-sm tabular">
              <thead>
                <tr className="text-left text-text-3">
                  <th className="py-1 font-normal">Market</th>
                  <th className="py-1 text-right font-normal">League average</th>
                  <th className="py-1 text-right font-normal">Ours</th>
                  <th className="py-1 text-right font-normal">Bookmaker</th>
                  <th className="py-1 text-right font-normal">Calibration error</th>
                </tr>
              </thead>
              <tbody>
                {GOALS_ROWS.map(([key, label]) => {
                  const g = bt.goals_markets![key];
                  if (!g) return null;
                  return (
                    <tr key={key} className="border-t border-border">
                      <td className="py-1.5">{label}</td>
                      <td className="py-1.5 text-right">{g.baseline.log_loss.toFixed(4)}</td>
                      <td className="py-1.5 text-right">{g.model.log_loss.toFixed(4)}</td>
                      <td className="py-1.5 text-right">{g.bookmaker ? g.bookmaker.bookmaker.log_loss.toFixed(4) : "–"}</td>
                      <td className="py-1.5 text-right text-text-2">
                        {(g.ece * 100).toFixed(1)} pts{" "}
                        <span className="text-text-3">(was {(g.ece_raw * 100).toFixed(1)})</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-text-3">
            Log loss, lower is better. Calibration error is the average gap between what we predicted and what
            happened, in percentage points. Bookmaker over/under odds are only available for the 2.5 line
            {bt.goals_markets.over_2_5?.bookmaker
              ? `, where the bookmaker was more accurate by ${bt.goals_markets.over_2_5.bookmaker.gap.mean.toFixed(3)} (95% interval ${bt.goals_markets.over_2_5.bookmaker.gap.ci_low.toFixed(3)} to ${bt.goals_markets.over_2_5.bookmaker.gap.ci_high.toFixed(3)})`
              : ""}
            .
          </p>
        </section>
      ) : null}

      {bt.asian_handicap ? (
        <section>
          <h3 className="mb-1 font-semibold">Asian handicap</h3>
          <p className="mb-3 max-w-2xl text-sm text-text-2">
            Every test match at its main line, home side. Win, push and lose are stake-weighted, so a half-win on a
            quarter line counts as half.
          </p>
          <table className="w-full max-w-md text-sm tabular">
            <thead>
              <tr className="text-left text-text-3">
                <th className="py-1 font-normal"></th>
                <th className="py-1 text-right font-normal">Win</th>
                <th className="py-1 text-right font-normal">Push</th>
                <th className="py-1 text-right font-normal">Lose</th>
              </tr>
            </thead>
            <tbody>
              {(["predicted", "actual"] as const).map((k) => (
                <tr key={k} className="border-t border-border">
                  <td className="py-1.5">{k === "predicted" ? "We predicted" : "Happened"}</td>
                  <td className="py-1.5 text-right">{pct(bt.asian_handicap![k].win)}</td>
                  <td className="py-1.5 text-right">{pct(bt.asian_handicap![k].push)}</td>
                  <td className="py-1.5 text-right">{pct(bt.asian_handicap![k].lose)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-2 max-w-2xl text-xs text-text-3">
            Over {bt.asian_handicap.n_matches.toLocaleString("en-GB")} matches, betting every main line at our own fair
            odds would have returned {signed(bt.asian_handicap.profit_at_fair)} per unit: the chances are well
            calibrated.
          </p>
          {bt.asian_handicap.vs_bookmaker ? (
            <div className="mt-4 max-w-2xl rounded-xl border border-border p-4 text-sm">
              <div className="font-semibold">Against the bookmakers&apos; closing handicap prices</div>
              <p className="mt-1 text-text-2">
                At each bookmaker&apos;s own closing line ({bt.asian_handicap.vs_bookmaker.n.toLocaleString("en-GB")}{" "}
                matches, pushes excluded) their prices were more accurate than ours: log loss{" "}
                {bt.asian_handicap.vs_bookmaker.bookmaker.toFixed(3)} against our{" "}
                {bt.asian_handicap.vs_bookmaker.ours.toFixed(3)} (lower is better; gap{" "}
                {signed(bt.asian_handicap.vs_bookmaker.gap.mean)}, 95% interval{" "}
                {signed(bt.asian_handicap.vs_bookmaker.gap.ci_low)} to {signed(bt.asian_handicap.vs_bookmaker.gap.ci_high)}).
              </p>
              {Object.entries(bt.asian_handicap.vs_bookmaker.value_bets).map(([k, v]) => (
                <p key={k} className="mt-2 text-text-2">
                  Backing our side whenever our fair odds beat their price ({k}):{" "}
                  <strong className="text-text">
                    {v.n.toLocaleString("en-GB")} bets, {v.profit_units >= 0 ? "+" : "−"}
                    {Math.abs(v.profit_units).toFixed(0)} units, ROI {v.roi >= 0 ? "+" : "−"}
                    {Math.abs(v.roi * 100).toFixed(1)}%
                  </strong>
                  .
                </p>
              ))}
              <p className="mt-2 text-xs text-text-3">
                In other words, when our handicap odds look better than the bookmaker&apos;s, it&apos;s usually our
                model that&apos;s wrong. Use our numbers as a guide, not as a source of value bets.
              </p>
            </div>
          ) : null}
        </section>
      ) : null}

      {bt.extra_markets ? (
        <section>
          <h3 className="mb-1 font-semibold">More markets</h3>
          <p className="mb-3 max-w-2xl text-sm text-text-2">
            Half-time, result-and-goals combinations, team goals and total goals, all priced from one scoreline model
            that matches our result and goals numbers. &ldquo;League average&rdquo; is each league&apos;s past
            frequency of each outcome, with no model. There are no bookmaker odds for these markets in our data.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full max-w-3xl text-sm tabular">
              <thead>
                <tr className="text-left text-text-3">
                  <th className="py-1 font-normal">Market</th>
                  <th className="py-1 text-right font-normal">Matches</th>
                  <th className="py-1 text-right font-normal">League average</th>
                  <th className="py-1 text-right font-normal">Ours</th>
                  <th className="py-1 text-right font-normal">Calibration error</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(bt.extra_markets).map(([k, v]) => {
                  const weak = v.model - v.baseline > -0.002;
                  return (
                    <tr key={k} className="border-t border-border">
                      <td className="py-1.5">
                        {v.label}
                        {weak ? <span className="ml-1.5 text-xs text-text-3">(no better than average)</span> : null}
                      </td>
                      <td className="py-1.5 text-right">{v.n.toLocaleString("en-GB")}</td>
                      <td className="py-1.5 text-right">{v.baseline.toFixed(4)}</td>
                      <td className={`py-1.5 text-right ${weak ? "" : "font-semibold text-win"}`}>{v.model.toFixed(4)}</td>
                      <td className="py-1.5 text-right text-text-2">{(v.ece * 100).toFixed(1)} pts</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-2 text-xs text-text-3">
            Log loss, lower is better; green = better than the league average. Calibration error is the average gap
            between predicted and actual frequency.
          </p>
        </section>
      ) : null}

      {/* 10-minute market hidden for now:
      {bt.half_time_check ? (
        <section>
          <h3 className="mb-1 font-semibold">10-minute result</h3>
          <p className="max-w-2xl text-sm text-text-2">
            The result after 10 minutes is estimated from each team&apos;s expected goals, scaled to the share of goals
            scored that early. Our data has no goal times, so these predictions can&apos;t be checked or tracked. We
            tested the same method at half-time, where real scores exist: over{" "}
            {bt.half_time_check.n.toLocaleString("en-GB")} matches it predicted {pct(bt.half_time_check.draw_predicted)}{" "}
            half-time draws and {pct(bt.half_time_check.draw_actual)} happened, and it beat each league&apos;s average
            half-time results (log loss {bt.half_time_check.model.log_loss.toFixed(3)} vs{" "}
            {bt.half_time_check.baseline.log_loss.toFixed(3)}). That supports the method, but the 10-minute numbers
            remain estimates.
          </p>
        </section>
      ) : null}
      */}

      <section>
        <h3 className="mb-2 font-semibold">How this was tested</h3>
        <ul className="max-w-2xl list-disc space-y-1.5 pl-5 text-sm text-text-2">
          <li>Each week&apos;s matches were predicted using only results from before that week.</li>
          <li>
            Every setting was chosen using seasons before {bt.test_seasons[0]}: the model settings, the blend of Elo
            and Dixon-Coles ({pct(bt.selection.blend_weight_elo)} Elo), whether to calibrate, and which model to use.
            The test seasons were never used to tune anything.
          </li>
          <li>
            The bookmaker benchmark is the closing odds with the bookmaker&apos;s margin removed: Pinnacle where
            available, otherwise the market average. Pinnacle odds stop partway through 2025-26.
          </li>
          <li>Log loss and Brier score measure how good the probabilities were, not just whether the favourite won.</li>
        </ul>
      </section>
    </>
  );
}

export default async function TrackRecordPage() {
  const [bt, doc, live, cbt] = await Promise.all([getBacktest(), getPredictions(), getLiveSummary(), getCornersBacktest()]);
  const leagueName = new Map(doc.leagues.map((l) => [l.code, l.name]));

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Track record</h1>
        <p className="mt-2 max-w-2xl text-text-2">
          How well the estimates have matched real results, compared with bookmaker closing odds. Those odds are a
          tough benchmark.
        </p>
      </div>

      {bt ? (
        <Backtest bt={bt} leagueName={leagueName} />
      ) : (
        <p className="rounded-lg border border-dashed border-border p-6 text-text-2">
          The backtest hasn&apos;t been run yet. Results will appear here once the models have been checked against
          past seasons.
        </p>
      )}

      {cbt ? <CornersRecord c={cbt} /> : null}

      <section>
        <h2 className="mb-3 text-lg font-semibold">Live predictions</h2>
        {live && live.n_logged_matches > 0 ? (
          <LiveRecord live={live} leagueName={leagueName} />
        ) : (
          <p className="rounded-lg border border-dashed border-border p-6 text-text-2">
            Nothing logged yet. Once logging starts, every prediction will be saved before kickoff and then scored
            against the result, so this record can&apos;t be edited after the fact.
          </p>
        )}
      </section>
    </div>
  );
}
