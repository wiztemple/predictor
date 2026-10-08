"use client";

import Link from "next/link";
import { useState } from "react";
import { formatShortDay, formatTime, pct } from "@/lib/format";
import { confidence, fairOdds } from "@/lib/markets";

export type PanelPick = {
  id: string;
  kickoff: string;
  kickoff_tbc: boolean;
  league_name: string;
  home: string;
  away: string;
  label: string;
  market: string;
  p: number;
  rank: number;
};

type Props = { picks: PanelPick[]; record: string | null; compact?: boolean; heading?: boolean };

/** Each day's top picks across all markets: the exact list we log and track. */
export function PicksPanel({ picks, record, compact = false, heading = true }: Props) {
  const days = [...new Set(picks.map((p) => formatShortDay(p.kickoff)))];
  const [day, setDay] = useState(days[0] ?? null);
  const shown = picks.filter((p) => formatShortDay(p.kickoff) === day).sort((a, b) => a.rank - b.rank);

  if (!picks.length) return null;
  return (
    <section className="rounded-2xl border border-border bg-surface p-4 sm:p-5">
      {heading ? (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h2 className="text-xl font-bold tracking-tight">Our likeliest picks</h2>
            <Link href="/picks" className="text-sm font-medium text-home hover:underline">
              Picks record →
            </Link>
          </div>
          <p className="mt-1 text-sm text-text-2">
            The single most likely bet in each match, any market. Top {Math.max(...picks.map((p) => p.rank))} per
            day.
            {record ? <span className="text-text-3"> {record}</span> : null}
          </p>
        </>
      ) : null}

      <div className={`flex gap-2 overflow-x-auto ${heading ? "mt-3" : ""}`}>
        {days.map((d) => (
          <button
            key={d}
            onClick={() => setDay(d)}
            aria-pressed={day === d}
            className={`shrink-0 rounded-full border px-3 py-1.5 text-sm whitespace-nowrap ${
              day === d ? "border-text bg-text text-surface" : "border-border text-text-2 hover:text-text"
            }`}
          >
            {d}
          </button>
        ))}
      </div>

      <ol className={`mt-3 grid gap-2 ${compact ? "" : "md:grid-cols-2"}`}>
        {shown.map((p) => {
          const c = confidence(p.p);
          return (
            <li key={p.id}>
              <Link
                href={`/match/${p.id}`}
                className="flex items-center gap-3 rounded-xl bg-surface-2 px-3 py-2.5 hover:ring-1 hover:ring-home"
              >
                <span className="w-5 shrink-0 text-center text-sm font-bold text-text-3 tabular">{p.rank}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-semibold">{p.label}</span>
                  <span className="block truncate text-xs text-text-3">
                    {p.home} v {p.away} · {p.league_name} · {formatTime(p.kickoff, p.kickoff_tbc)}
                  </span>
                </span>
                <span className="shrink-0 text-right tabular">
                  <span className="block text-lg leading-tight font-bold">{pct(p.p)}</span>
                  <span className="block text-[11px] text-text-3">@{fairOdds(p.p)}</span>
                </span>
                <span
                  className={`hidden shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium sm:inline ${
                    c.level === 3 ? "bg-home text-white" : c.level === 2 ? "bg-home/15 text-home" : "bg-surface text-text-2"
                  }`}
                >
                  {c.label}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
