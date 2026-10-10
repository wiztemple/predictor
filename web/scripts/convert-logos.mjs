// Rasterise team logos to small square WebPs: node scripts/convert-logos.mjs plan.json
// plan.json: [{ "src": "/abs/in.svg", "dest": "/abs/out.webp" }, ...]
// Rasterising also strips anything active an SVG could carry (scripts, external links).
import { readFileSync, statSync } from "node:fs";
import sharp from "sharp";

const SIZE = 128;
const plan = JSON.parse(readFileSync(process.argv[2], "utf8"));
let done = 0;
let skipped = 0;
for (const { src, dest } of plan) {
  try {
    if (statSync(dest).mtimeMs >= statSync(src).mtimeMs) {
      skipped++;
      continue;
    }
  } catch {
    // dest missing: convert
  }
  try {
    await sharp(src, { density: 300 })
      .resize(SIZE, SIZE, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .webp({ quality: 85 })
      .toFile(dest);
    done++;
  } catch (e) {
    console.error(`FAIL ${src}: ${e.message}`);
    process.exitCode = 1;
  }
}
console.log(`convert-logos: ${done} converted, ${skipped} up to date`);
