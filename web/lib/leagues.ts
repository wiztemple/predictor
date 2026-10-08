// Presentation-only grouping of league codes by country, in display order.
export const COUNTRIES: { country: string; codes: string[] }[] = [
  { country: "England", codes: ["E0", "E1"] },
  { country: "Spain", codes: ["SP1", "SP2"] },
  { country: "Italy", codes: ["I1", "I2"] },
  { country: "Germany", codes: ["D1", "D2"] },
  { country: "France", codes: ["F1", "F2"] },
  { country: "Netherlands", codes: ["N1"] },
  { country: "Portugal", codes: ["P1"] },
  { country: "Scotland", codes: ["SC0"] },
  { country: "Belgium", codes: ["B1"] },
  { country: "Turkey", codes: ["T1"] },
  { country: "Greece", codes: ["G1"] },
  { country: "Austria", codes: ["AUT"] },
  { country: "Switzerland", codes: ["SWZ"] },
  { country: "Denmark", codes: ["DNK"] },
  { country: "Poland", codes: ["POL"] },
  { country: "Romania", codes: ["ROU"] },
];

const ORDER = new Map(COUNTRIES.flatMap((c) => c.codes).map((code, i) => [code, i]));
export const leagueOrder = (code: string) => ORDER.get(code) ?? 999;
