#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
MUSE_TALK_DIR="${MUSE_TALK_DIR:-$PWD/.runtime/MuseTalk}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
MUSE_TALK_PORT="${MUSE_TALK_PORT:-8090}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg is required" >&2; exit 1; }

if [[ ! -d "$MUSE_TALK_DIR/.git" ]]; then
  mkdir -p "$(dirname "$MUSE_TALK_DIR")"
  git clone --depth 1 https://github.com/TMElyralab/MuseTalk.git "$MUSE_TALK_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
if [[ "${MUSE_TALK_INSTALL_OFFICIAL_TORCH:-false}" == "true" ]]; then
  "$PYTHON_BIN" -m pip install \
    torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cu118
fi
"$PYTHON_BIN" -m pip install -r "$MUSE_TALK_DIR/requirements.txt"
"$PYTHON_BIN" -m pip install --no-cache-dir -U openmim
mim install mmengine
mim install "mmcv==2.0.1"
mim install "mmdet==3.1.0"
mim install "mmpose==1.1.0"
"$PYTHON_BIN" -m pip install -r "$PROJECT_ROOT/workers/musetalk_http/requirements.txt"

if [[ ! -f "$MUSE_TALK_DIR/models/musetalkV15/unet.pth" ]]; then
  (cd "$MUSE_TALK_DIR" && sh ./download_weights.sh)
fi

export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export MUSE_TALK_DIR
export MUSE_TALK_FFMPEG_PATH="$(dirname "$(command -v ffmpeg)")"
export MUSE_TALK_API_KEY="${MUSE_TALK_API_KEY:-demo-lip-sync-token}"

echo "Starting MuseTalk HTTP provider on port $MUSE_TALK_PORT"
exec "$PYTHON_BIN" -m uvicorn workers.musetalk_http.app:app \
  --host 0.0.0.0 \
  --port "$MUSE_TALK_PORT"
