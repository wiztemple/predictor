# web

The website. It only shows predictions the Python pipeline has already made;
nothing is computed in the browser or on a server. Every page is pre-rendered
and exported as static files (`out/`), which Cloudflare Workers serves.

## Data

The site reads only from `web/data/`:

| File | Written by |
| --- | --- |
| `data/predictions/predictions.json` | `scripts/predict_fixtures.py` |
| `data/predictions/live_summary.json` | `scripts/score_predictions.py` |
| `data/backtest/summary.json` | `scripts/backtest.py` |
| `data/picks/summary.json` | `scripts/settle_picks.py` (from the picks database) |
| `data/picks/backtest.json` | `scripts/backtest_picks.py` |

The scheduled run copies these files from `../data`, and `pnpm dev` and
`pnpm build` refresh the copy too (`scripts/sync-data.mjs`). Because of this,
the site builds from `web/` on its own.

## Commands

```bash
pnpm install
pnpm dev       # http://localhost:3000
pnpm build     # static export to out/
pnpm preview   # serve out/ the way Cloudflare does (wrangler dev)
pnpm deploy    # manual deploy (wrangler deploy); normally Cloudflare builds on push
```

## Cloudflare

`wrangler.jsonc` deploys `out/` as a static-assets Worker. The site is served
at `https://predictor.<account>.workers.dev`; a custom domain can be added
later in the dashboard.

Cloudflare builds on every push to `main`, including the data commits from the
scheduled run, with these settings:

| Setting | Value |
| --- | --- |
| Root directory | `web` |
| Build command | `pnpm build` |
| Deploy command | `npx wrangler deploy` |
