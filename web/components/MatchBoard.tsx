"use client";

import Link from "next/link";
import { useState } from "react";
import { formatShortDay, formatTime, pct } from "@/lib/format";
import { type BoardMatch, type MarketKey, CORNER_LINES, MARKETS, bestCell, cells, fairOdds, isCorners } from "@/lib/markets";
import type { Threshold } from "@/lib/picks";
import { useUrlParam } from "@/lib/useUrlParam";
import { leagueColor } from "@/lib/leagues";
import { OutcomeCell } from "./OutcomeCell";
import { ConfidenceBadge, LeagueDot, TeamBadge } from "./ui";

export type TrackTables = Partial<Record<MarketKey, { over?: Threshold[]; under?: Threshold[] }>>;

type Props = { matches: BoardMatch[]; leagues: { code: string; name: string }[]; track: TrackTables };

const chip = (active: boolean) =>
  `shrink-0 rounded-full border px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors ${
    active
      ? "tab-active"
      : "border-border bg-surface text-text-2 hover:border-accent hover:text-accent"
  }`;

/** Which threshold table applies to a pick, by the option picked. */
function sideOf(market: MarketKey, label: string): "over" | "under" {
  if (market === "1x2") return "over";
  return label === "Under" || label === "NG" ? "under" : "over";
}

function trackLine(market: MarketKey, picks: { cell: { label: string; p: number } }[], track: TrackTables) {
  if (!picks.length) return null;
  if (market === "ten") return "Estimated from expected goals. Our data has no goal times, so there's no track record.";
  const side = sideOf(market, picks[0].cell.label);
  const floor = Math.min(...picks.filter((x) => sideOf(market, x.cell.label) === side).map((x) => x.cell.p));
  const t = (track[market]?.[side] ?? [])
    .filter((r) => r.min_p <= floor + 1e-9 && r.n >= 30)
    .sort((a, b) => b.min_p - a.min_p)[0];
  if (!t) return null;
  return `Our past ${pct(t.min_p)}+ picks here came in ${pct(t.hit_rate)} of the time (${t.n.toLocaleString("en-GB")} matches).`;
}

export function MatchBoard({ matches, leagues, track }: Props) {
  // ?m=o25 links straight to a market (shareable) and stays in sync as the user switches.
  const [m, setM] = useUrlParam("m");
  const market: MarketKey = MARKETS.some((x) => x.key === m) ? (m as MarketKey) : "1x2";
  const setMarket = (k: MarketKey) => setM(k === "1x2" ? null : k);
  const days = [...new Set(matches.map((m) => formatShortDay(m.kickoff)))];
  // open on the next match day; "All days" is one tap away
  const [day, setDay] = useState<string | null>(days[0] ?? null);
  const [league, setLeague] = useState<string | null>(null);
  const [minP, setMinP] = useState(0); // show only matches whose top option reaches this chance
  const leagueCount = new Map<string, number>();
  for (const m of matches) leagueCount.set(m.league, (leagueCount.get(m.league) ?? 0) + 1);

  const corners = isCorners(market);
  const noCorners = corners ? [...new Set(matches.filter((m) => !m.corners).map((m) => m.league_name))] : [];
  const shown = matches.filter(
    (m) =>
      (!corners || m.corners) &&
      (!day || formatShortDay(m.kickoff) === day) &&
      (!league || m.league === league) &&
      (minP === 0 || Math.round((bestCell(m, market)?.p ?? 0) * 100) >= minP * 100),
  );
  // main AH lines sit near 50/50 by design, so a "top picks" list would just be coin flips
  const picks =
    market === "cs" || market === "ah"
      ? []
      : shown
          .map((m) => ({ m, cell: bestCell(m, market)! }))
          .filter((x) => x.cell)
          .sort((a, b) => b.cell.p - a.cell.p)
          .slice(0, 10);
  const marketLabel = MARKETS.find((x) => x.key === market)!.label;
  const line = trackLine(market, picks, track);

  // day -> league -> matches, leagues in display order
  const order = new Map(leagues.map((l, i) => [l.code, i]));
  const byDay = new Map<string, Map<string, BoardMatch[]>>();
  for (const m of shown) {
    const d = formatShortDay(m.kickoff);
    if (!byDay.has(d)) byDay.set(d, new Map());
    const g = byDay.get(d)!;
    if (!g.has(m.league)) g.set(m.league, []);
    g.get(m.league)!.push(m);
  }

  return (
    <div>
      {/* controls */}
      <div className="z-10 -mx-4 border-b border-border bg-page/90 px-4 pt-3 pb-3 backdrop-blur sm:sticky sm:top-0">
        <div role="tablist" aria-label="Market" className="flex gap-1 overflow-x-auto rounded-xl border border-border bg-surface p-1">
          {[...MARKETS.filter((mk) => !mk.group), { key: "c8.5" as MarketKey, short: "Corners" }].map((mk) => {
            const active = mk.short === "Corners" ? corners : market === mk.key;
            return (
              <button
                key={mk.short}
                role="tab"
                aria-selected={active}
                onClick={() => (mk.short === "Corners" && corners ? null : setMarket(mk.key))}
                className={`flex-1 shrink-0 rounded-lg px-3 py-2 text-sm font-semibold whitespace-nowrap transition-colors ${
                  active ? "tab-active" : "text-text-2 hover:text-text"
                }`}
              >
                {mk.short}
              </button>
            );
          })}
        </div>
        {corners ? (
          <div className="mt-2 flex items-center gap-2 overflow-x-auto" aria-label="Corners line">
            <span className="shrink-0 text-xs font-medium text-text-3">Total corners over/under</span>
            {CORNER_LINES.map((l) => (
              <button
                key={l}
                className={chip(market === `c${l}`)}
                aria-pressed={market === `c${l}`}
                onClick={() => setMarket(`c${l}` as MarketKey)}
              >
                {l}
              </button>
            ))}
          </div>
        ) : null}
        <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 gap-2 overflow-x-auto">
            <button className={chip(day === null)} aria-pressed={day === null} onClick={() => setDay(null)}>
              All days
            </button>
            {days.map((d) => (
              <button key={d} className={chip(day === d)} aria-pressed={day === d} onClick={() => setDay(day === d ? null : d)}>
                {d}
              </button>
            ))}
          </div>
          <div className="flex shrink-0 gap-2">
            <select
              aria-label="Minimum chance"
              value={minP}
              onChange={(e) => setMinP(Number(e.target.value))}
              className="flex-1 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-text-2"
            >
              <option value={0}>Any chance</option>
              <option value={0.6}>60%+ only</option>
              <option value={0.7}>70%+ only</option>
              <option value={0.8}>80%+ only</option>
            </select>
            {leagues.length > 1 ? (
              <select
                aria-label="League"
                value={league ?? ""}
                onChange={(e) => setLeague(e.target.value || null)}
                className="flex-1 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-text-2"
              >
                <option value="">All leagues ({matches.length})</option>
                {leagues
                  .filter((l) => leagueCount.has(l.code))
                  .map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.name} ({leagueCount.get(l.code)})
                    </option>
                  ))}
              </select>
            ) : null}
          </div>
        </div>
      </div>

      {noCorners.length ? (
        <p className="mt-3 text-xs text-text-3">
          No corner data for {noCorners.join(", ")}, so those matches are left out of this tab.
        </p>
      ) : null}

      {/* top picks */}
      {picks.length > 0 ? (
        <section className="mt-4">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h2 className="text-base font-bold">
              Top picks <span className="text-accent">· {marketLabel}</span>
            </h2>
            {line ? <p className="text-xs text-text-3">{line}</p> : null}
          </div>
          <ol className="mt-2 flex snap-x gap-2 overflow-x-auto pb-2">
            {picks.map(({ m, cell }, i) => {
              return (
                <li key={m.id} className="w-48 shrink-0 snap-start">
                  <Link
                    href={`/match/${m.id}`}
                    className="flex h-full flex-col rounded-xl border border-border bg-surface p-2.5 transition hover:border-accent"
                  >
                    <div className="flex items-center justify-between text-xs text-text-3">
                      <span className="truncate">
                        #{i + 1} · {m.league_name}
                      </span>
                      <span className="shrink-0 tabular">
                        {formatShortDay(m.kickoff)} {formatTime(m.kickoff, m.kickoff_tbc)}
                      </span>
                    </div>
                    <div className="mt-1.5 flex items-center gap-1 truncate text-xs text-text-2">
                      <TeamBadge name={m.home} size="xs" />
                      <TeamBadge name={m.away} size="xs" />
                      <span className="truncate">
                        {m.home} v {m.away}
                      </span>
                    </div>
                    <div className="mt-0.5 truncate text-sm font-semibold">{cell.pickLabel}</div>
                    <div className="mt-auto flex items-end justify-between pt-1.5">
                      <div className="tabular">
                        <span className="text-lg font-extrabold">{pct(cell.p)}</span>
                        <span className="ml-1 text-[11px] text-text-3">@{fairOdds(cell.p)}</span>
                      </div>
                      <ConfidenceBadge p={cell.p} />
                    </div>
                  </Link>
                </li>
              );
            })}
          </ol>
        </section>
      ) : null}

      {/* all matches */}
      <div className="mt-4 space-y-6">
        {shown.length === 0 ? <p className="text-text-3">No matches for this filter.</p> : null}
        {[...byDay.entries()].map(([d, groups]) => (
          <section key={d}>
            <h2 className="text-sm font-bold uppercase tracking-wide text-text-2">{d}</h2>
            {/* league cards: one column on phones, two (newspaper-style) on wide screens */}
            <div className="mt-2 gap-3 lg:columns-2 [&>*]:mb-3 [&>*]:break-inside-avoid">
              {[...groups.entries()]
                .sort((a, b) => (order.get(a[0]) ?? 999) - (order.get(b[0]) ?? 999))
                .map(([code, list]) => (
                  <div key={code} className="overflow-hidden rounded-xl border border-border bg-surface">
                    <div className="flex items-center justify-between border-b border-border px-3 py-1.5 text-xs">
                      <span className="flex items-center gap-2 font-bold text-text">
                        <LeagueDot color={leagueColor(code)} code={code} />
                        {list[0].league_name}
                      </span>
                      <span className="text-text-3">{marketLabel}</span>
                    </div>
                    <ul className="divide-y divide-border">
                      {list.map((m) => (
                        <li key={m.id}>
                          <BoardRow m={m} market={market} />
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function BoardRow({ m, market }: { m: BoardMatch; market: MarketKey }) {
  const cs = cells(m, market);
  const best = bestCell(m, market)?.label;
  const top = m.scores[0];
  const extra =
    isCorners(market) && m.corners
      ? { label: "Exp. corners", value: m.corners.total.toFixed(1) }
      : top && market !== "cs" && market !== "ten"
        ? { label: "Likely score", value: `${top.home}-${top.away}` }
        : null;
  // one line per match on every screen: time | teams | (likely score, wider screens) | odds
  return (
    <Link href={`/match/${m.id}`} className="flex items-center gap-2 px-3 py-2 hover:bg-surface-2 sm:gap-3">
      <span className="w-9 shrink-0 text-[11px] text-text-3 tabular">{formatTime(m.kickoff, m.kickoff_tbc)}</span>
      <div className="min-w-0 flex-1 space-y-0.5 text-sm">
        <div className="flex items-center gap-1.5 font-medium">
          <TeamBadge name={m.home} size="xs" />
          <span className="truncate">{m.home}</span>
        </div>
        <div className="flex items-center gap-1.5 font-medium">
          <TeamBadge name={m.away} size="xs" />
          <span className="truncate">{m.away}</span>
        </div>
      </div>
      {extra ? (
        <span className="hidden w-14 shrink-0 text-center text-[10px] leading-tight text-text-3 sm:block">
          {extra.label}
          <span className="block text-sm font-semibold text-text tabular">{extra.value}</span>
        </span>
      ) : null}
      <div className={`grid w-36 shrink-0 gap-1 sm:w-56 lg:w-44 ${cs.length === 2 ? "grid-cols-2" : "grid-cols-3"}`}>
        {cs.map((c) => (
          <OutcomeCell key={c.label} label={c.label} p={c.p} best={c.label === best} compact />
        ))}
      </div>
    </Link>
  );
}
