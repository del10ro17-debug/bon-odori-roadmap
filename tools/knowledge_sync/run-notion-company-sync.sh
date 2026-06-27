#!/bin/bash
set -euo pipefail

NODE_BIN="${HOME}/.nvm/versions/node/v24.15.0/bin/node"
SCRIPT="${HOME}/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian/scripts/notion-company-sync.js"
LOG="/tmp/notion-company-sync.log"

echo "[$(date '+%H:%M:%S')] notion-company-sync start" >> "$LOG"
"$NODE_BIN" "$SCRIPT" "$@" >> "$LOG" 2>&1
echo "[$(date '+%H:%M:%S')] notion-company-sync done" >> "$LOG"
