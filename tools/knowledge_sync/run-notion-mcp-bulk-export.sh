#!/bin/bash
# Notion MCP 経由で AI ミーティングノート等を .raw/ に一括エクスポート
# 前提: Cursor で Notion MCP 認証済み、claude CLI は /login 済み

set -euo pipefail

VAULT="/Users/sho_sakakura/Library/Mobile Documents/iCloud~md~Obsidian/Documents/claude-obsidian"
PROMPT="$VAULT/../company-hq/tools/knowledge_sync/prompts/notion-mcp-bulk-export.md"
CLAUDE="$HOME/.nvm/versions/node/v24.15.0/bin/claude"
LOG="/tmp/notion-mcp-bulk-export.log"

if [[ ! -f "$PROMPT" ]]; then
  PROMPT="/Users/sho_sakakura/company-hq/tools/knowledge_sync/prompts/notion-mcp-bulk-export.md"
fi

echo "[$(date '+%H:%M:%S')] notion-mcp-bulk-export start" >> "$LOG"
cd "$VAULT"
"$CLAUDE" -p "$(cat "$PROMPT")" --dangerously-skip-permissions >> "$LOG" 2>&1
echo "[$(date '+%H:%M:%S')] notion-mcp-bulk-export done" >> "$LOG"
