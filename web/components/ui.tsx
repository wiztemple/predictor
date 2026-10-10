import leagueLogos from "@/data/league_logos.json";
import logos from "@/data/team_logos.json";
import { confidence } from "@/lib/markets";

// Team name -> /teams/<slug>.webp, written by scripts/import_logos.py.
const LOGOS: Record<string, string> = logos;
// League code -> /leagues/<code>.webp (same script).
const LEAGUE_LOGOS: Record<string, string> = leagueLogos;

// Deep, saturated badge colours: white initials stay readable (>= 4.5:1) on all of them.
const BADGE = ["#0e7490", "#be185d", "#b91c1c", "#c2410c", "#b45309", "#15803d", "#0f766e", "#0369a1", "#1d4ed8", "#334155", "#4d7c0f", "#a16207"];
const SKIP = new Set(["fc", "ac", "as", "sc", "cf", "cd", "rc", "afc", "the", "de", "1."]);

function hash(s: string) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

export function initials(name: string) {
  const words = name.replace(/['.]/g, "").split(/\s+/).filter((w) => w && !SKIP.has(w.toLowerCase()));
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return (words[0] ?? name).slice(0, 2).toUpperCase();
}

/** The team's logo when we have one, else a coloured circle with its initials (same team, same colour,
 *  everywhere). Decorative: the name always sits next to it. */
export function TeamBadge({ name, size = "sm" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "size-12 text-base" : size === "md" ? "size-8 text-xs" : "size-6 text-[10px]";
  const logo = LOGOS[name];
  if (logo) {
    const px = size === "lg" ? 48 : size === "md" ? 32 : 24;
    // eslint-disable-next-line @next/next/no-img-element -- static export: plain <img>, files are pre-sized
    return <img src={logo} alt="" aria-hidden width={px} height={px} loading="lazy" className={`shrink-0 object-contain ${dim}`} />;
  }
  return (
    <span
      aria-hidden
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-bold text-white ${dim}`}
      style={{ background: BADGE[hash(name) % BADGE.length] }}
    >
      {initials(name)}
    </span>
  );
}

const TONE = {
  3: "bg-surface text-conf-3 ring-conf-3/40",
  2: "bg-surface text-conf-2 ring-conf-2/40",
  1: "bg-surface text-conf-1 ring-conf-1/40",
  0: "bg-surface text-text-3 ring-border",
} as const;
const BAR = { 3: "bg-conf-3", 2: "bg-conf-2", 1: "bg-conf-1", 0: "bg-text-3" } as const;

/** "Very likely" / "Likely" / "Lean" tag, coloured by tier (the label carries the meaning too). */
export function ConfidenceBadge({ p }: { p: number }) {
  const c = confidence(p);
  return (
    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ${TONE[c.level]}`}>
      {c.label}
    </span>
  );
}

/** Thin bar showing the chance, in the confidence colour. */
export function ConfidenceBar({ p, className = "" }: { p: number; className?: string }) {
  const c = confidence(p);
  return (
    <span aria-hidden className={`block h-1.5 overflow-hidden rounded-full bg-border ${className}`}>
      <span className={`block h-full rounded-full ${BAR[c.level]}`} style={{ width: `${Math.round(p * 100)}%` }} />
    </span>
  );
}

/** Small coloured square for a league's country. */
/** The competition's logo when we have one, else a small square in the league's colour. Decorative. */
export function LeagueDot({ color, code }: { color: string; code?: string }) {
  const logo = code ? LEAGUE_LOGOS[code] : undefined;
  if (logo) {
    // eslint-disable-next-line @next/next/no-img-element -- static export: plain <img>, files are pre-sized
    return <img src={logo} alt="" aria-hidden width={18} height={18} loading="lazy" className="size-[18px] shrink-0 object-contain" />;
  }
  return <span aria-hidden className="inline-block size-2.5 shrink-0 rounded-sm" style={{ background: color }} />;
}
