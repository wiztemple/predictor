"use client";

import Link from "next/link";
import { type CSSProperties, useState } from "react";
import { formatShortDay, formatTime, pct } from "@/lib/format";
import { fairOdds } from "@/lib/markets";
import { ConfidenceBadge, ConfidenceBar, TeamBadge } from "./ui";

// gold / silver / bronze for the top three
const MEDAL: Record<number, CSSProperties> = {
  1: { background: "#fbbf24", color: "#451a03" },
  2: { background: "#cbd5e1", color: "#1e293b" },
  3: { background: "#f0a46b", color: "#431407" },
};

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
    <section className="rounded-2xl border-2 border-accent/50 bg-surface">
      <div className="p-4 sm:p-5">
      {heading ? (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
            <h2 className="text-xl font-extrabold tracking-tight">
              <span className="text-accent">Our likeliest picks</span>
            </h2>
            <Link href="/picks" className="text-sm font-semibold text-accent hover:underline">
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
            className={`shrink-0 rounded-full border px-3 py-1.5 text-sm font-medium whitespace-nowrap transition-colors ${
              day === d
                ? "bg-text border-transparent text-page shadow-sm"
                : "border-border text-text-2 hover:border-accent hover:text-accent"
            }`}
          >
            {d}
          </button>
        ))}
      </div>

      <ol className={`mt-3 grid gap-2 ${compact ? "" : "md:grid-cols-2"}`}>
        {shown.map((p) => (
          <li key={p.id}>
            <Link
              href={`/match/${p.id}`}
              className="flex items-center gap-3 rounded-xl border border-border bg-surface-2/60 px-3 py-2.5 transition hover:-translate-y-0.5 hover:border-accent hover:shadow-md"
            >
              <span
                className="flex size-7 shrink-0 items-center justify-center rounded-full text-sm font-extrabold tabular"
                style={MEDAL[p.rank] ?? { background: "var(--surface)", color: "var(--text-3)" }}
              >
                {p.rank}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-bold">{p.label}</span>
                <span className="mt-0.5 flex items-center gap-1.5 truncate text-xs text-text-3">
                  <TeamBadge name={p.home} />
                  <span className="truncate">
                    {p.home} v {p.away} · {p.league_name} · {formatTime(p.kickoff, p.kickoff_tbc)}
                  </span>
                </span>
                <ConfidenceBar p={p.p} className="mt-1.5" />
              </span>
              <span className="shrink-0 text-right tabular">
                <span className="block text-lg leading-tight font-extrabold">{pct(p.p)}</span>
                <span className="block text-[11px] text-text-3">@{fairOdds(p.p)}</span>
              </span>
              <span className="hidden sm:inline">
                <ConfidenceBadge p={p.p} />
              </span>
            </Link>
          </li>
        ))}
      </ol>
      </div>
    </section>
  );
}
