#!/usr/bin/env bash
set -euo pipefail

PYTHON_BINARY="${PYTHON_BINARY:-python3}"
VOICE_NAME="${PIPER_VOICE_NAME:-ar_JO-kareem-medium}"
SITE_DIR="${PIPER_SITE_DIR:-$PWD/.runtime/piper-site}"
MODEL_DIR="${PIPER_DATA_DIR:-$PWD/.runtime/piper-models}"
HOST="${PIPER_HOST:-127.0.0.1}"
PORT="${PIPER_PORT:-8001}"

if [[ ! -d "$SITE_DIR" ]]; then
  echo "Piper runtime is missing. Run scripts/setup_demo_piper.sh first." >&2
  exit 1
fi

export PYTHONPATH="$SITE_DIR${PYTHONPATH:+:$PYTHONPATH}"
if ! "$PYTHON_BINARY" -c 'import fastapi, piper, uvicorn' >/dev/null 2>&1; then
  echo "Piper packages are incomplete in: $SITE_DIR" >&2
  echo "Run scripts/setup_demo_piper.sh again." >&2
  exit 1
fi

export PIPER_VOICE_NAME="$VOICE_NAME"
export PIPER_DATA_DIR="$MODEL_DIR"
export PIPER_SAMPLE_RATE="${PIPER_SAMPLE_RATE:-22050}"
export PIPER_API_KEY="${PIPER_API_KEY:-}"

exec "$PYTHON_BINARY" -m uvicorn app:app \
  --app-dir "$PWD/workers/piper_compat" \
  --host "$HOST" \
  --port "$PORT"
