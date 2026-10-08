export const TIME_ZONE = "Europe/London";
export const TIME_ZONE_LABEL = "UK time";

const dayFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: TIME_ZONE,
  weekday: "long",
  day: "numeric",
  month: "long",
});
const timeFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: TIME_ZONE,
  hour: "2-digit",
  minute: "2-digit",
});
const shortFmt = new Intl.DateTimeFormat("en-GB", {
  timeZone: TIME_ZONE,
  weekday: "short",
  day: "numeric",
  month: "short",
});

export const formatDay = (iso: string) => dayFmt.format(new Date(iso));
export const formatShortDay = (iso: string) => shortFmt.format(new Date(iso));
export const formatTime = (iso: string, tbc = false) => (tbc ? "TBC" : timeFmt.format(new Date(iso)));

/** 0.4396 -> "44%". Probabilities, never odds or certainties. */
export const pct = (p: number) => `${Math.round(p * 100)}%`;

/** Precise variant for small values: 0.0123 -> "1.2%". */
export const pct1 = (p: number) => (p < 0.1 ? `${(p * 100).toFixed(1)}%` : pct(p));

export const MODEL_LABELS: Record<string, string> = {
  blend: "Elo + Dixon-Coles blend",
  dixon_coles: "Dixon-Coles",
  elo: "Elo",
};
export const modelLabel = (name: string) => MODEL_LABELS[name] ?? name;

/** Group already-sorted items by UK calendar day. */
export function groupByDay<T extends { kickoff: string }>(items: T[]) {
  const groups = new Map<string, T[]>();
  for (const item of items) {
    const key = formatDay(item.kickoff);
    const list = groups.get(key);
    if (list) list.push(item);
    else groups.set(key, [item]);
  }
  return [...groups.entries()];
}
