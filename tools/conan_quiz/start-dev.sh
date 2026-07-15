#!/bin/zsh
# 名探偵コナン クイズを同じWi-Fiのスマホで開けるようにする
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
QUIZ_DIR="$ROOT_DIR/docs/conan-quiz"
PORT="${1:-8765}"

LOCAL_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"

echo ""
echo "=== 名探偵コナン クイズ ==="
echo "同じWi-Fiのスマホのブラウザで開いてください"
echo ""
if [[ -n "$LOCAL_IP" ]]; then
  echo "  http://${LOCAL_IP}:${PORT}/"
else
  echo "  http://（MacのIP）:${PORT}/"
  echo "  ※ Wi-Fi IPが取れませんでした。システム設定でIPを確認してください"
fi
echo ""
echo "止めるときは Ctrl+C"
echo ""

cd "$QUIZ_DIR"
exec python3 -m http.server "$PORT" --bind 0.0.0.0
