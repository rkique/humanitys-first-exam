#!/usr/bin/env bash
# Weekly snapshot refresh, meant to be triggered by cron on the deployed VM.
# Resolves paths relative to its own location so it works regardless of
# where the repo is checked out (e.g. /root/coffee, /home/deploy/coffee).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$SCRIPT_DIR/weekly_fetch.log"

cd "$PROJECT_DIR"

echo "==== $(date -u '+%Y-%m-%d %H:%M:%S UTC') starting weekly fetch ====" >> "$LOG_FILE"

if python3 fetch_models.py >> "$LOG_FILE" 2>&1; then
  echo "==== $(date -u '+%Y-%m-%d %H:%M:%S UTC') done ====" >> "$LOG_FILE"
else
  status=$?
  echo "==== $(date -u '+%Y-%m-%d %H:%M:%S UTC') FAILED (exit $status) ====" >> "$LOG_FILE"
  exit "$status"
fi
