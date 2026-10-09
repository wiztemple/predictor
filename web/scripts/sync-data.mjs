// Copy the pipeline's published files from ../data into ./data so the site
// builds from its own folder (Vercel builds the web service on its own).
// No-op when ../data isn't there, e.g. in a deploy that only has web/.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";

const FILES = [
  "predictions/predictions.json",
  "predictions/live_summary.json",
  "backtest/summary.json",
  "backtest/corners.json",
  "picks/summary.json",
  "picks/backtest.json",
  "picks/weekly.json",
];

const src = join(process.cwd(), "..", "data");
if (existsSync(src)) {
  let n = 0;
  for (const f of FILES) {
    if (!existsSync(join(src, f))) continue;
    mkdirSync(dirname(join("data", f)), { recursive: true });
    copyFileSync(join(src, f), join("data", f));
    n++;
  }
  console.log(`sync-data: copied ${n} file(s) from ../data`);
}
