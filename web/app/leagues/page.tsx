import type { Metadata } from "next";
import Link from "next/link";
import { COUNTRIES } from "@/lib/leagues";
import { getPredictions } from "@/lib/predictions";

export const metadata: Metadata = { title: "Leagues" };

export default async function LeaguesPage() {
  const doc = await getPredictions();
  const name = new Map(doc.leagues.map((l) => [l.code, l.name]));
  const count = new Map<string, number>();
  for (const p of doc.predictions) count.set(p.league, (count.get(p.league) ?? 0) + 1);
  const known = new Set(doc.leagues.map((l) => l.code));

  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Leagues</h1>
      <p className="mt-2 max-w-2xl text-text-2">
        {doc.leagues.length} leagues. Some leagues only list their fixtures a few days before each round, so a league
        with no upcoming matches yet will fill in nearer the time.
      </p>
      <div className="mt-8 grid gap-x-8 gap-y-6 sm:grid-cols-2 lg:grid-cols-3">
        {COUNTRIES.filter((c) => c.codes.some((code) => known.has(code))).map((c) => (
          <section key={c.country}>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-text-3">{c.country}</h2>
            <ul className="mt-2 divide-y divide-border border-y border-border">
              {c.codes.filter((code) => known.has(code)).map((code) => (
                <li key={code}>
                  <Link href={`/league/${code}`} className="flex items-baseline justify-between gap-3 py-2.5 hover:bg-surface-2">
                    <span className="font-medium">{name.get(code)}</span>
                    <span className="text-sm text-text-3 tabular">
                      {count.get(code) ? `${count.get(code)} upcoming` : "none listed yet"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
