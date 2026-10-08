import { pct1 } from "@/lib/format";

type Props = {
  cells: number[][];
  other: number;
  home: string;
  away: string;
};

/** Scoreline probability heatmap: rows = home goals, columns = away goals.
 *  Single-hue sequential ramp; every cell also prints its value. */
export function ScoreGrid({ cells, other, home, away }: Props) {
  let max = 0;
  for (const row of cells) for (const v of row) if (v > max) max = v;
  const goals = cells.map((_, i) => i);

  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-0.5 text-xs tabular">
        <caption className="mb-2 text-left text-sm text-text-2">
          Rows: <span className="font-medium text-text">{home}</span> goals. Columns:{" "}
          <span className="font-medium text-text">{away}</span> goals.
        </caption>
        <thead>
          <tr>
            <th scope="col" className="p-1 text-text-3 font-normal">
              <span className="sr-only">Home goals by away goals</span>
            </th>
            {goals.map((g) => (
              <th key={g} scope="col" className="w-12 p-1 text-center font-medium text-text-2">
                {g}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cells.map((row, i) => (
            <tr key={i}>
              <th scope="row" className="pr-2 text-right font-medium text-text-2">
                {i}
              </th>
              {row.map((p, j) => {
                const t = max > 0 ? p / max : 0;
                return (
                  <td
                    key={j}
                    title={`${home} ${i}-${j} ${away}: ${pct1(p)}`}
                    className="h-9 w-12 rounded text-center"
                    style={{
                      background: `color-mix(in oklab, var(--seq-hi) ${Math.round(t * 85)}%, var(--surface-2))`,
                      color: t > 0.55 ? "#ffffff" : "var(--text)",
                    }}
                  >
                    {p >= 0.0005 ? pct1(p) : "·"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-text-3">
        Scores above {cells.length - 1} goals for either side: {pct1(other)} combined.
      </p>
    </div>
  );
}
