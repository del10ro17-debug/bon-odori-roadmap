#!/usr/bin/env bash
# Idempotent dependency install for Cursor Cloud Agents.
# Runs from the repository root (environment.json "install").
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[cloud-install] repo root: $ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[cloud-install] ERROR: python3 not found" >&2
  exit 1
fi

# Ensure venv module exists (base cloud images sometimes omit it)
if ! python3 -c "import ensurepip, venv" >/dev/null 2>&1; then
  echo "[cloud-install] python3-venv missing; attempting apt install"
  if command -v sudo >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3-venv python3.12-venv >/dev/null
  else
    echo "[cloud-install] ERROR: cannot install python3-venv without sudo" >&2
    exit 1
  fi
fi

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip

REQ_FILES=(
  apps/maruke-app/requirements.txt
  tools/creative_visual/requirements.txt
  tools/wangan_price_db/requirements.txt
)

for req in "${REQ_FILES[@]}"; do
  if [[ -f "$req" ]]; then
    echo "[cloud-install] pip install -r $req"
    pip install -r "$req"
  else
    echo "[cloud-install] skip missing $req"
  fi
done

# Optional Cloudflare Workers tooling (user-local; no root required)
if command -v npm >/dev/null 2>&1; then
  echo "[cloud-install] npm install wrangler (user prefix)"
  mkdir -p "$HOME/.local"
  npm install -g wrangler --prefix "$HOME/.local" >/dev/null
  export PATH="$HOME/.local/bin:$PATH"
  if ! grep -qF '$HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
  fi
else
  echo "[cloud-install] skip wrangler (npm not found)"
fi

echo "[cloud-install] verifying imports"
python -c "import fastapi, uvicorn, PIL, fitz, matplotlib; print('python deps ok')"

echo "[cloud-install] python: $(python --version)"
echo "[cloud-install] node: $(node --version 2>/dev/null || echo n/a)"
echo "[cloud-install] wrangler: $(command -v wrangler >/dev/null && wrangler --version || echo 'not on PATH yet (open new shell)')"
echo "[cloud-install] done"
