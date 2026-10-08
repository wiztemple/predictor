# web

The Next.js frontend for the predictor. It only displays predictions that the
Python pipeline has already computed. No model runs in the browser.

It reads these files at build time:

| File | Written by |
| --- | --- |
| `../data/predictions/predictions.json` | `scripts/predict_fixtures.py` |
| `../data/backtest/summary.json` | the Step 3 backtest (optional; the page shows an empty state until it exists) |

To read them from somewhere else, set `PREDICTIONS_PATH` and `BACKTEST_PATH`.

```bash
pnpm install
pnpm dev          # http://localhost:3000; refresh the page to pick up new data
pnpm build && pnpm start
```

| Route | Content |
| --- | --- |
| `/` | Every league with its next matches |
| `/league/[code]` | Fixtures for one league, grouped by day |
| `/match/[id]` | Win/draw/loss chances for one match from both models, goals markets and the full scoreline grid |
| `/track-record` | Backtest results and logged live predictions |

All pages are statically generated. After regenerating `predictions.json`,
rebuild the site so it shows the new data.
