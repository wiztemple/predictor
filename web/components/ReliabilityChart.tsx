import type { ReliabilityBin } from "@/lib/trackRecord";
import { pct } from "@/lib/format";

const SERIES = [
  { key: "home", label: "Home win", color: "var(--home)" },
  { key: "draw", label: "Draw", color: "var(--draw)" },
  { key: "away", label: "Away win", color: "var(--away)" },
] as const;

const W = 360;
const H = 360;
const PAD = { l: 44, r: 12, t: 12, b: 40 };
const TICKS = [0, 0.2, 0.4, 0.6, 0.8, 1];
const x = (v: number) => PAD.l + v * (W - PAD.l - PAD.r);
const y = (v: number) => H - PAD.b - v * (H - PAD.t - PAD.b);

/** Predicted probability (x) vs how often it happened (y). On the diagonal = well calibrated.
 *  Bins with fewer than `minN` matches are hidden as too noisy. */
export function ReliabilityChart({ bins, minN = 30 }: { bins: ReliabilityBin[]; minN?: number }) {
  const shown = bins.filter((b) => b.n >= minN);
  return (
    <figure>
      <div className="mb-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-2">
        {SERIES.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5">
            <span aria-hidden className="inline-block size-2 rounded-full" style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
        <span className="flex items-center gap-1.5">
          <span aria-hidden className="inline-block w-4 border-t border-dashed border-text-3" />
          Perfect calibration
        </span>
      </div>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full max-w-sm"
        role="img"
        aria-label="Reliability chart: predicted probability against how often it happened. A table version follows."
      >
        {TICKS.map((t) => (
          <g key={t}>
            <line x1={x(0)} x2={x(1)} y1={y(t)} y2={y(t)} stroke="var(--border)" strokeWidth={1} />
            <text x={PAD.l - 8} y={y(t)} dy="0.32em" textAnchor="end" fontSize={11} fill="var(--text-3)">
              {pct(t)}
            </text>
            <text x={x(t)} y={H - PAD.b + 16} textAnchor="middle" fontSize={11} fill="var(--text-3)">
              {pct(t)}
            </text>
          </g>
        ))}
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--text-3)" strokeDasharray="4 4" strokeWidth={1} />
        <text x={x(0.5)} y={H - 4} textAnchor="middle" fontSize={11} fill="var(--text-2)">
          Predicted probability
        </text>
        <text transform={`translate(11 ${y(0.5)}) rotate(-90)`} textAnchor="middle" fontSize={11} fill="var(--text-2)">
          How often it happened
        </text>
        {SERIES.map((s) => {
          const pts = shown.filter((b) => b.outcome === s.key);
          return (
            <g key={s.key}>
              <polyline
                points={pts.map((b) => `${x(b.mean_pred).toFixed(1)},${y(b.observed).toFixed(1)}`).join(" ")}
                fill="none"
                stroke={s.color}
                strokeWidth={2}
              />
              {pts.map((b) => (
                <circle
                  key={b.bin_lo}
                  cx={x(b.mean_pred)}
                  cy={y(b.observed)}
                  r={4}
                  fill={s.color}
                  stroke="var(--surface)"
                  strokeWidth={2}
                >
                  <title>{`${s.label}: predicted ${pct(b.mean_pred)}, happened ${pct(b.observed)} (${b.n} matches)`}</title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
    </figure>
  );
}
