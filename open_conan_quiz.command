#!/bin/bash
# 名探偵コナン クイズを同じWi-Fiの子どものスマホで開く
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/tools/conan_quiz/start-dev.sh"
