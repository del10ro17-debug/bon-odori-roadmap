#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}"
exec "$ROOT_DIR/tools/maruke_app/start-dev.sh"
