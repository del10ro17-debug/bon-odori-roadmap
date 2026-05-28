#!/bin/bash
# attendance-api.gs をクリップボードにコピー（Apps Script へ手動貼り付け用）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FILE="$ROOT/docs/bon-odori/attendance-api.gs"
pbcopy < "$FILE"
osascript -e 'display notification "Cmd+A → Cmd+V → Cmd+S で Apps Script に貼り付け" with title "盆踊り GAS コードをコピーしました"'
