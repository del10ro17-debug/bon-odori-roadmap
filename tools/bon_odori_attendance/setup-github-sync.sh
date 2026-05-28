#!/bin/bash
# 1回だけ実行: GitHub CLI でログイン後、このスクリプトで自動共有を有効化する
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DATA_JS="$ROOT/docs/bon-odori/data.js"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) が必要です: brew install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub にログインしてください:"
  gh auth login
fi

TOKEN="$(gh auth token)"
if [ -z "$TOKEN" ]; then
  echo "トークンを取得できませんでした。"
  exit 1
fi

node - "$DATA_JS" "$TOKEN" <<'NODE'
const fs = require("fs");
const [file, token] = process.argv.slice(2);
let s = fs.readFileSync(file, "utf8");
const escaped = token.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
if (/attendanceGithubToken:\s*"/.test(s)) {
  s = s.replace(/attendanceGithubToken:\s*"[^"]*"/, `attendanceGithubToken: "${escaped}"`);
} else {
  s = s.replace(
    /attendanceApiUrl:\s*"[^"]*"/,
    (m) => `${m},\n  attendanceGithubRepo: "del10ro17-debug/bon-odori-roadmap",\n  attendanceGithubBranch: "main",\n  attendanceGithubPath: "docs/bon-odori/attendance.json",\n  attendanceGithubToken: "${escaped}"`
  );
}
fs.writeFileSync(file, s);
console.log("Updated attendanceGithubToken in data.js");
NODE

echo ""
echo "完了。次: git add docs/bon-odori/data.js && git commit && git push"
echo "（トークンは公開リポジトリに入ります。bon-odori-roadmap のみ書き込み権限の PAT を推奨）"
