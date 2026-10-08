#!/usr/bin/env bash
# Full refresh: data -> dataset -> checks -> predictions (+ log) -> live scoring.
# Safe to run from cron; stops at the first failing step.
#   crontab example (daily 05:30 UTC, plus Fri-Sun 10:30 for late kickoff-time changes):
#   30 5 * * *   cd /path/to/predictor && scripts/update.sh >> data/update.log 2>&1
#   30 10 * * 5-7 cd /path/to/predictor && scripts/update.sh >> data/update.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"

echo "=== update $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
"$PY" scripts/download_data.py
"$PY" scripts/build_dataset.py
"$PY" scripts/check_data.py
"$PY" scripts/predict_fixtures.py
"$PY" scripts/score_predictions.py
"$PY" scripts/settle_picks.py
echo "=== done ==="
