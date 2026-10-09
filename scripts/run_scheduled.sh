#!/usr/bin/env bash
# Scheduled run on this machine (launchd): refresh + predict + log + settle, then
# publish the fresh data to GitHub so the site rebuilds. Safe to run by hand.
set -uo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# one run at a time
LOCK="/tmp/predictor-update.lock"
if ! mkdir "$LOCK" 2>/dev/null; then echo "another run is in progress; skipping"; exit 0; fi
trap 'rmdir "$LOCK"' EXIT

echo "=== scheduled run $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
if ! scripts/update.sh; then
  echo "update failed; nothing published"
  exit 1
fi

# Mondays, first run of the day: extend the backtest with last week's results
if [ "$(date +%u)" = "1" ] && [ "$(date +%H)" -lt 10 ]; then
  .venv/bin/python scripts/backtest.py --refresh && .venv/bin/python scripts/backtest_picks.py && .venv/bin/python scripts/backtest_corners.py
fi

(cd web && node scripts/sync-data.mjs)
git add data/predictions data/backtest/summary.json data/backtest/report.md data/backtest/corners.json data/models data/picks web/data
if git diff --cached --quiet; then
  echo "no data changes to publish"
else
  git commit -q -m "Refresh predictions $(date -u +%Y-%m-%dT%H:%MZ)" && git push -q && echo "published to GitHub"
fi
echo "=== done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
