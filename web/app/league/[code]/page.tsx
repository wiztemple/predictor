import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { MatchBoard } from "@/components/MatchBoard";
import { toBoardMatch, trackTables } from "@/lib/board";
import { TIME_ZONE_LABEL } from "@/lib/format";
import { getLeague, getPredictions } from "@/lib/predictions";
import { getBacktest } from "@/lib/trackRecord";

export async function generateStaticParams() {
  const doc = await getPredictions();
  return doc.leagues.map((l) => ({ code: l.code }));
}

export async function generateMetadata({ params }: PageProps<"/league/[code]">): Promise<Metadata> {
  const data = await getLeague((await params).code);
  return { title: data?.league.name ?? "League" };
}

export default async function LeaguePage({ params }: PageProps<"/league/[code]">) {
  const [data, bt] = await Promise.all([getLeague((await params).code), getBacktest()]);
  if (!data) notFound();
  const { league, matches } = data;

  return (
    <div>
      <Link href="/leagues" className="text-sm text-accent font-semibold hover:underline">
        ← All leagues
      </Link>
      <h1 className="mt-3 text-2xl font-bold tracking-tight">{league.name}</h1>
      <p className="mt-1 text-sm text-text-2">
        {matches.length} upcoming match{matches.length === 1 ? "" : "es"} · times {TIME_ZONE_LABEL}
      </p>
      {matches.length === 0 ? (
        <p className="mt-8 rounded-xl border border-dashed border-border p-6 text-text-2">
          No fixtures listed yet. This league publishes its fixtures a few days before each round, so check back nearer
          the weekend.
        </p>
      ) : (
        <div className="mt-4">
          <MatchBoard
            matches={matches.map(toBoardMatch)}
            leagues={[{ code: league.code, name: league.name }]}
            track={trackTables(bt)}
          />
        </div>
      )}
    </div>
  );
}
