#!/usr/bin/env bash
set -euo pipefail

LOG="/tmp/career-gmail-sync.log"
ERR="/tmp/career-gmail-sync-error.log"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

{
  echo "=== $(date -Iseconds) career-gmail-sync start ==="
  python3 "$SCRIPT_DIR/sync_career_gmail.py"
  echo "=== $(date -Iseconds) career-gmail-sync ok ==="
} >>"$LOG" 2>>"$ERR"
