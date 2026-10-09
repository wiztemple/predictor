// Betting-style markets built from a match's probabilities. Fair odds = 1 / probability.
import { type Margin, ahChance, awayOf, fmtLine, homeOutcome, mainLine } from "./handicap";

export type CornerKey = "c7.5" | "c8.5" | "c9.5" | "c10.5" | "c11.5";
export type MarketKey = "1x2" | "ten" | "ht" | "dnb" | "o15" | "o25" | "gg" | "ah" | "cs" | CornerKey;

/** Total-corners lines offered; the board shows one Corners tab with these as sub-options. */
export const CORNER_LINES = ["7.5", "8.5", "9.5", "10.5", "11.5"] as const;
export const isCorners = (k: MarketKey): k is CornerKey => k.startsWith("c") && k !== "cs";

export type BoardMatch = {
  id: string;
  league: string;
  league_name: string;
  kickoff: string;
  kickoff_tbc: boolean;
  home: string;
  away: string;
  probabilities: { home: number; draw: number; away: number };
  over_1_5?: number;
  over_2_5?: number;
  btts?: number;
  scores: { home: number; away: number; p: number }[]; // top 3
  margin?: Margin;
  ten?: { home: number; draw: number; away: number }; // result after 10 minutes (estimate)
  ht?: Record<string, number>; // half-time result: "1" | "X" | "2"
  dnb?: Record<string, number>; // draw no bet: "1" | "2"
  corners?: { total: number; over: Record<string, number> }; // expected total, P(over line)
};

export type Cell = { label: string; p: number; pickLabel: string };

export const MARKETS: { key: MarketKey; label: string; short: string; group?: "corners" }[] = [
  { key: "1x2", label: "Match result", short: "1X2" },
  // 10-minute market hidden for now (uncomment to bring back the 10′ tab):
  // { key: "ten", label: "Result after 10 minutes", short: "10′" },
  { key: "ht", label: "Half-time result", short: "HT" },
  { key: "dnb", label: "Draw no bet", short: "DNB" },
  { key: "o15", label: "Over/Under 1.5", short: "O/U 1.5" },
  { key: "o25", label: "Over/Under 2.5", short: "O/U 2.5" },
  { key: "gg", label: "Both teams to score", short: "GG/NG" },
  { key: "ah", label: "Asian handicap (main line)", short: "AH" },
  { key: "cs", label: "Correct score", short: "Score" },
  ...CORNER_LINES.map((l) => ({
    key: `c${l}` as CornerKey,
    label: `Corners over/under ${l}`,
    short: `Corners ${l}`,
    group: "corners" as const,
  })),
];

export const fairOdds = (p: number) => (p > 0 ? (1 / p).toFixed(2) : "–");

export function cells(m: BoardMatch, market: MarketKey): Cell[] {
  const { home, draw, away } = m.probabilities;
  const ou = (p: number | undefined, line: string): Cell[] =>
    p === undefined
      ? []
      : [
          { label: "Over", p, pickLabel: `Over ${line}` },
          { label: "Under", p: 1 - p, pickLabel: `Under ${line}` },
        ];
  switch (market) {
    case "1x2":
      return [
        { label: "1", p: home, pickLabel: `${m.home} win` },
        { label: "X", p: draw, pickLabel: "Draw" },
        { label: "2", p: away, pickLabel: `${m.away} win` },
      ];
    case "ten":
      return m.ten
        ? [
            { label: "1", p: m.ten.home, pickLabel: `${m.home} ahead at 10′` },
            { label: "X", p: m.ten.draw, pickLabel: "Draw at 10′" },
            { label: "2", p: m.ten.away, pickLabel: `${m.away} ahead at 10′` },
          ]
        : [];
    case "ht":
      return m.ht
        ? [
            { label: "1", p: m.ht["1"], pickLabel: `${m.home} leads at HT` },
            { label: "X", p: m.ht["X"], pickLabel: "Level at HT" },
            { label: "2", p: m.ht["2"], pickLabel: `${m.away} leads at HT` },
          ]
        : [];
    case "dnb":
      return m.dnb
        ? [
            { label: "1", p: m.dnb["1"], pickLabel: `${m.home} (draw no bet)` },
            { label: "2", p: m.dnb["2"], pickLabel: `${m.away} (draw no bet)` },
          ]
        : [];
    case "o15":
      return ou(m.over_1_5, "1.5");
    case "o25":
      return ou(m.over_2_5, "2.5");
    case "gg":
      return m.btts === undefined
        ? []
        : [
            { label: "GG", p: m.btts, pickLabel: "Both teams score" },
            { label: "NG", p: 1 - m.btts, pickLabel: "Not both score" },
          ];
    case "ah": {
      if (!m.margin) return [];
      const line = mainLine(m.margin);
      const h = homeOutcome(m.margin, line);
      return [
        { label: `1 ${fmtLine(line)}`, p: ahChance(h), pickLabel: `${m.home} ${fmtLine(line)}` },
        { label: `2 ${fmtLine(-line)}`, p: ahChance(awayOf(h)), pickLabel: `${m.away} ${fmtLine(-line)}` },
      ];
    }
    case "cs":
      return m.scores.map((s) => ({ label: `${s.home}-${s.away}`, p: s.p, pickLabel: `Score ${s.home}-${s.away}` }));
    default: {
      const line = market.slice(1);
      const p = m.corners?.over[line];
      return p === undefined
        ? []
        : [
            { label: "Over", p, pickLabel: `Over ${line} corners` },
            { label: "Under", p: 1 - p, pickLabel: `Under ${line} corners` },
          ];
    }
  }
}

/** The single most likely option in a market for one match. */
export function bestCell(m: BoardMatch, market: MarketKey): Cell | null {
  const cs = cells(m, market);
  return cs.length ? cs.reduce((a, b) => (b.p > a.p ? b : a)) : null;
}

/** Confidence wording bettors can scan; thresholds are on the probability itself. */
export function confidence(p: number): { label: string; level: 0 | 1 | 2 | 3 } {
  if (p >= 0.8) return { label: "Very likely", level: 3 };
  if (p >= 0.65) return { label: "Likely", level: 2 };
  if (p >= 0.5) return { label: "Lean", level: 1 };
  return { label: "Open", level: 0 };
}
