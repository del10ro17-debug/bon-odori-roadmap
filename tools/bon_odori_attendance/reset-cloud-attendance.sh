#!/bin/bash
# クラウドの参加可否を本番2件だけに戻す（GAS に __reset 対応コードをデプロイ済みであること）
set -euo pipefail
API="https://script.google.com/macros/s/AKfycbzjEZdccMcKy8xDL3A0m3mb-BLU4MFuIdzflVsAA6yxAoFZ_OE3oRbll5nHOdtrWOgTaA/exec"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PAYLOAD="$(python3 - "$ROOT/docs/bon-odori/attendance.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
print(json.dumps({"__reset": True, "responses": data["responses"]}, ensure_ascii=False))
PY
)"
curl -sS -L -X POST "$API" \
  -H "Content-Type: text/plain;charset=utf-8" \
  -d "$PAYLOAD" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK:', [r['name'] for r in d.get('responses',[])])"
