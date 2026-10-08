// Presentation-only grouping of league codes by country, in display order.
export const COUNTRIES: { country: string; codes: string[]; color: string }[] = [
  { country: "England", color: "#dc2626", codes: ["E0", "E1"] },
  { country: "Spain", color: "#f59e0b", codes: ["SP1", "SP2"] },
  { country: "Italy", color: "#16a34a", codes: ["I1", "I2"] },
  { country: "Germany", color: "#ca8a04", codes: ["D1", "D2"] },
  { country: "France", color: "#2563eb", codes: ["F1", "F2"] },
  { country: "Netherlands", color: "#f97316", codes: ["N1"] },
  { country: "Portugal", color: "#be123c", codes: ["P1"] },
  { country: "Scotland", color: "#1d4ed8", codes: ["SC0"] },
  { country: "Belgium", color: "#e11d48", codes: ["B1"] },
  { country: "Turkey", color: "#ef4444", codes: ["T1"] },
  { country: "Greece", color: "#0ea5e9", codes: ["G1"] },
  { country: "Austria", color: "#f43f5e", codes: ["AUT"] },
  { country: "Switzerland", color: "#b91c1c", codes: ["SWZ"] },
  { country: "Denmark", color: "#0891b2", codes: ["DNK"] },
  { country: "Poland", color: "#db2777", codes: ["POL"] },
  { country: "Romania", color: "#eab308", codes: ["ROU"] },
];

const ORDER = new Map(COUNTRIES.flatMap((c) => c.codes).map((code, i) => [code, i]));
export const leagueOrder = (code: string) => ORDER.get(code) ?? 999;

const COLOR = new Map(COUNTRIES.flatMap((c) => c.codes.map((code) => [code, c.color] as const)));
/** Country colour for a league code (decorative accent; the league name is always shown). */
export const leagueColor = (code: string) => COLOR.get(code) ?? "#64748b";
