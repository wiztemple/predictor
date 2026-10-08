import { confidence } from "@/lib/markets";

// Deep, saturated badge colours: white initials stay readable (>= 4.5:1) on all of them.
const BADGE = ["#6d28d9", "#be185d", "#b91c1c", "#c2410c", "#b45309", "#15803d", "#0f766e", "#0369a1", "#1d4ed8", "#4338ca", "#7e22ce", "#9d174d"];
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

/** Coloured circle with a team's initials; same team, same colour, everywhere. Decorative (name sits next to it). */
export function TeamBadge({ name, size = "sm" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? "size-12 text-base" : size === "md" ? "size-8 text-xs" : "size-6 text-[10px]";
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
  3: "bg-conf-3/15 text-conf-3 ring-conf-3/30",
  2: "bg-conf-2/15 text-conf-2 ring-conf-2/30",
  1: "bg-conf-1/15 text-conf-1 ring-conf-1/30",
  0: "bg-surface-2 text-text-3 ring-border",
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
    <span aria-hidden className={`block h-1.5 overflow-hidden rounded-full bg-surface-2 ${className}`}>
      <span className={`block h-full rounded-full ${BAR[c.level]}`} style={{ width: `${Math.round(p * 100)}%` }} />
    </span>
  );
}

/** Small coloured square for a league's country. */
export function LeagueDot({ color }: { color: string }) {
  return <span aria-hidden className="inline-block size-2.5 shrink-0 rounded-sm" style={{ background: color }} />;
}
