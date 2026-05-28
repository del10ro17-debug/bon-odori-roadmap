#!/bin/bash
# 1回だけ実行: 自動共有APIをデプロイし data.js を更新（トークンはリポジトリに入れない）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DATA_JS="$ROOT/docs/bon-odori/data.js"
WORKER_DIR="$ROOT/workers/bon-odori-attendance"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) が必要です: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub にログインしてください:"
  gh auth login
fi

SYNC_KEY="$(openssl rand -hex 16)"
echo "同期キーを生成しました（data.js にのみ記載・GitHubトークンは保存しません）"

cd "$WORKER_DIR"

if ! npx wrangler@3 whoami >/dev/null 2>&1; then
  echo ""
  echo "Cloudflare にログインしてください（無料アカウントでOK）:"
  npx wrangler@3 login
fi

echo "KV 名前空間を作成中..."
KV_OUT="$(npx wrangler@3 kv:namespace create ATTENDANCE 2>&1 || true)"
KV_ID="$(echo "$KV_OUT" | grep -Eo '[a-f0-9]{32}' | tail -1)"

if [ -z "$KV_ID" ]; then
  echo "KV の作成に失敗しました。手動: cd workers/bon-odori-attendance && npx wrangler kv:namespace create ATTENDANCE"
  exit 1
fi

sed -i '' "s/id = \"REPLACE_ME\"/id = \"$KV_ID\"/" wrangler.toml 2>/dev/null || \
  sed -i "s/id = \"REPLACE_ME\"/id = \"$KV_ID\"/" wrangler.toml

printf '%s' "$SYNC_KEY" | npx wrangler@3 secret put SYNC_KEY

echo "Worker をデプロイ中..."
DEPLOY_LOG="$(npx wrangler@3 deploy 2>&1)"
echo "$DEPLOY_LOG"

WORKER_URL="$(echo "$DEPLOY_LOG" | grep -Eo 'https://[a-zA-Z0-9.-]+\.workers\.dev' | head -1)"
if [ -z "$WORKER_URL" ]; then
  WORKER_URL="$(npx wrangler@3 deployments list 2>/dev/null | grep -Eo 'https://[a-zA-Z0-9.-]+\.workers\.dev' | head -1 || true)"
fi

if [ -z "$WORKER_URL" ]; then
  echo "Worker URL を取得できませんでした。wrangler deploy の出力を確認してください。"
  exit 1
fi

node - "$DATA_JS" "$WORKER_URL" "$SYNC_KEY" <<'NODE'
const fs = require("fs");
const [file, apiUrl, syncKey] = process.argv.slice(2);
let s = fs.readFileSync(file, "utf8");
s = s.replace(/attendanceApiUrl:\s*"[^"]*"/, `attendanceApiUrl: "${apiUrl}"`);
if (/attendanceSyncKey:\s*"/.test(s)) {
  s = s.replace(/attendanceSyncKey:\s*"[^"]*"/, `attendanceSyncKey: "${syncKey}"`);
} else {
  s = s.replace(
    /attendanceApiUrl:\s*"[^"]*"/,
    (m) => `${m},\n  attendanceSyncKey: "${syncKey}"`
  );
}
s = s.replace(/attendanceGithubToken:\s*"[^"]*"/, 'attendanceGithubToken: ""');
fs.writeFileSync(file, s);
console.log("Updated data.js:");
console.log("  attendanceApiUrl =", apiUrl);
console.log("  attendanceSyncKey = (set)");
NODE

echo ""
echo "完了。次を実行してください:"
echo "  cd $ROOT"
echo "  git add docs/bon-odori/data.js workers/bon-odori-attendance/wrangler.toml"
echo "  git commit -m \"Enable attendance sync via Cloudflare Worker\""
echo "  git push origin main"
