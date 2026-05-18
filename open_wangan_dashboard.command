#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"
cd "$ROOT_DIR"

DB_PATH="data/wangan_prices.sqlite"
DASHBOARD_DATA="docs/wangan-price-dashboard/data.js"
DASHBOARD_HTML="docs/wangan-price-dashboard/index.html"

echo "湾岸マンション売出価格ダッシュボードを準備しています..."

if [[ ! -f "$DB_PATH" ]]; then
  echo "ローカルDBが見つからないため、origin/main から復元を試します。"
  mkdir -p data
  if git show origin/main:data/wangan_prices.sqlite > "$DB_PATH" 2>/dev/null; then
    echo "DBを復元しました: $DB_PATH"
  else
    echo ""
    echo "DBを自動取得できませんでした。"
    echo "先にGmail同期またはGitHub Actionsで data/wangan_prices.sqlite を作成してください。"
    echo ""
    echo "詳しくは docs/wangan-price-db.md を確認してください。"
    echo ""
    read "?Enterキーで閉じます。"
    exit 1
  fi
fi

python3 tools/wangan_price_db/export_dashboard_data.py \
  --db "$DB_PATH" \
  --output "$DASHBOARD_DATA"

open "$DASHBOARD_HTML"

echo "ダッシュボードを開きました。"
