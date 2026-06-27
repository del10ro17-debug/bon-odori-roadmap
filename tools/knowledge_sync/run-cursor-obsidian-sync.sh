#!/bin/bash
# 手動: Cursor 会話 → Obsidian（日次ジョブと同じ transcript 部分のみ）
set -euo pipefail
NODE="${HOME}/.nvm/versions/node/v24.15.0/bin/node"
exec "$NODE" "$(cd "$(dirname "$0")" && pwd)/cursor-transcript-sync.js" "$@"
