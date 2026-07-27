#!/usr/bin/env bash
set -euo pipefail

VOICE_NAME="${PIPER_VOICE_NAME:-ar_JO-kareem-medium}"
VENV_DIR="${PIPER_VENV_DIR:-$PWD/.runtime/piper-venv}"
MODEL_DIR="${PIPER_DATA_DIR:-$PWD/.runtime/piper-models}"
HOST="${PIPER_HOST:-127.0.0.1}"
PORT="${PIPER_PORT:-8001}"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Piper runtime is missing. Run scripts/setup_demo_piper.sh first." >&2
  exit 1
fi

export PIPER_VOICE_NAME="$VOICE_NAME"
export PIPER_DATA_DIR="$MODEL_DIR"
export PIPER_SAMPLE_RATE="${PIPER_SAMPLE_RATE:-22050}"
export PIPER_API_KEY="${PIPER_API_KEY:-}"

exec "$VENV_DIR/bin/python" -m uvicorn app:app \
  --app-dir "$PWD/workers/piper_compat" \
  --host "$HOST" \
  --port "$PORT"
