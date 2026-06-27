#!/bin/bash
# Cursor → Obsidian は日次 com.user.cursor-daily-sync (08:30) に一本化。
# 旧 30分 LaunchAgent が残っていれば停止する。
set -euo pipefail

LABEL="com.user.cursor-transcript-sync"
PLIST_DST="$HOME/Library/LaunchAgents/${LABEL}.plist"

if launchctl print "gui/$(id -u)/${LABEL}" &>/dev/null; then
  launchctl bootout "gui/$(id -u)" "$PLIST_DST" 2>/dev/null || true
  echo "Stopped ${LABEL} (was 30-min interval)"
fi
rm -f "$PLIST_DST"

echo "Cursor → Obsidian: daily via com.user.cursor-daily-sync at 08:30 JST"
echo "  → transcript + plans + git commits → wiki/sources/cursor/ + .raw/"
echo "Manual now: node tools/knowledge_sync/cursor-transcript-sync.js"
echo "Logs: /tmp/cursor-daily-sync.log"
