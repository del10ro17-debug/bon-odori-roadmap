#!/bin/bash
# 坂倉さんPCで1回実行: GitHubトークンをブラウザに保存（リポジトリには載せない）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) が必要です: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub にログインしてください:"
  gh auth login
fi

TOKEN="$(gh auth token)"
PAGE="https://del10ro17-debug.github.io/bon-odori-roadmap/bon-odori/?setup_token=${TOKEN}"

echo ""
echo "ブラウザで共有設定を完了します…"
open "$PAGE"

echo ""
echo "完了したら、このトークンを家族の端末でも使えます（LINEで共有可）:"
echo "$TOKEN"
echo ""
echo "※ トークンは公開リポジトリに入れません。各端末の「共有設定」に貼り付けてもOKです。"
read -r -p "Enter で終了"
