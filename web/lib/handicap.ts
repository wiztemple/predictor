// Asian handicap from the goal-difference distribution in predictions.json.
// Mirrors src/predictor/handicap.py (tested there). Lines are the HOME handicap.

export type Margin = { cap: number; probs: number[] }; // probs[i] = P(home - away = i - cap), ends are tails

export type AhOutcome = { win: number; push: number; lose: number };

function split(line: number): [number, number] {
  const q = Math.round(line * 4);
  return q % 2 !== 0 ? [(q - 1) / 4, (q + 1) / 4] : [line, line];
}

/** Stake-weighted win / push / lose for the HOME side at `line` (quarter lines count half each way). */
export function homeOutcome(m: Margin, line: number): AhOutcome {
  let win = 0, push = 0, lose = 0;
  for (const part of split(line)) {
    m.probs.forEach((p, i) => {
      const adj = i - m.cap + part;
      if (Math.abs(adj) < 1e-9) push += p / 2;
      else if (adj > 0) win += p / 2;
      else lose += p / 2;
    });
  }
  return { win, push, lose };
}

export const awayOf = (o: AhOutcome): AhOutcome => ({ win: o.lose, push: o.push, lose: o.win });

/** Zero-EV decimal odds when a push returns the stake. */
export const ahFairOdds = (o: AhOutcome) => (o.win > 0 ? 1 + o.lose / o.win : Infinity);

/** Push-adjusted chance (1 / fair odds) - comparable with plain win chances. */
export const ahChance = (o: AhOutcome) => 1 / ahFairOdds(o);

/** Quarter-step home line with fair odds closest to evens: the "main line". */
export function mainLine(m: Margin): number {
  let best = 0, gap = Infinity;
  for (let q = -12; q <= 12; q++) {
    const o = homeOutcome(m, q / 4);
    if (o.win <= 0 || o.lose <= 0) continue;
    const g = Math.abs(Math.log(ahFairOdds(o) / 2));
    if (g < gap - 1e-12) { best = q / 4; gap = g; }
  }
  return best;
}

/** "-0.75", "+1", "0" */
export function fmtLine(line: number): string {
  if (Math.abs(line) < 1e-9) return "0";
  return `${line > 0 ? "+" : "−"}${Math.abs(line).toFixed(2).replace(/\.?0+$/, "")}`;
}
