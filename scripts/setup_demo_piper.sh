#!/usr/bin/env bash
set -euo pipefail

PYTHON_BINARY="${PYTHON_BINARY:-python3}"
VOICE_NAME="${PIPER_VOICE_NAME:-ar_JO-kareem-medium}"
VENV_DIR="${PIPER_VENV_DIR:-$PWD/.runtime/piper-venv}"
MODEL_DIR="${PIPER_DATA_DIR:-$PWD/.runtime/piper-models}"

mkdir -p "$PWD/.runtime" "$MODEL_DIR"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  "$PYTHON_BINARY" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r workers/piper_compat/requirements.txt

MODEL_PATH="$MODEL_DIR/$VOICE_NAME.onnx"
CONFIG_PATH="$MODEL_DIR/$VOICE_NAME.onnx.json"
if [[ ! -s "$MODEL_PATH" || ! -s "$CONFIG_PATH" ]]; then
  "$VENV_DIR/bin/python" -m piper.download_voices \
    --data-dir "$MODEL_DIR" \
    "$VOICE_NAME"
fi

printf 'PIPER_RUNTIME_READY=%s\n' "$VENV_DIR"
printf 'PIPER_MODEL_READY=%s\n' "$MODEL_PATH"
