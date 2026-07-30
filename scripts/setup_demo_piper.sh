#!/usr/bin/env bash
set -euo pipefail

PYTHON_BINARY="${PYTHON_BINARY:-python3}"
VOICE_NAME="${PIPER_VOICE_NAME:-ar_JO-kareem-medium}"
SITE_DIR="${PIPER_SITE_DIR:-$PWD/.runtime/piper-site}"
MODEL_DIR="${PIPER_DATA_DIR:-$PWD/.runtime/piper-models}"
REQUIREMENTS_PATH="${PIPER_REQUIREMENTS_PATH:-$PWD/workers/piper_compat/requirements.txt}"

mkdir -p "$PWD/.runtime" "$MODEL_DIR"

piper_python() {
  PYTHONPATH="$SITE_DIR${PYTHONPATH:+:$PYTHONPATH}" "$PYTHON_BINARY" "$@"
}

if ! piper_python -c 'import fastapi, piper, uvicorn' >/dev/null 2>&1; then
  echo "Installing Piper into the project-local package directory: $SITE_DIR"
  rm -rf "$SITE_DIR"
  mkdir -p "$SITE_DIR"
  "$PYTHON_BINARY" -m pip install \
    --disable-pip-version-check \
    --no-input \
    --upgrade \
    --target "$SITE_DIR" \
    -r "$REQUIREMENTS_PATH"
fi

piper_python -c 'import fastapi, piper, uvicorn' >/dev/null

MODEL_PATH="$MODEL_DIR/$VOICE_NAME.onnx"
CONFIG_PATH="$MODEL_DIR/$VOICE_NAME.onnx.json"
if [[ ! -s "$MODEL_PATH" || ! -s "$CONFIG_PATH" ]]; then
  piper_python -m piper.download_voices \
    --data-dir "$MODEL_DIR" \
    "$VOICE_NAME"
fi

printf 'PIPER_RUNTIME_READY=%s\n' "$SITE_DIR"
printf 'PIPER_MODEL_READY=%s\n' "$MODEL_PATH"
