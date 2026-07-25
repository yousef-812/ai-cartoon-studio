#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-$PWD/.runtime/ComfyUI}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
COMFYUI_PORT="${COMFYUI_PORT:-8188}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v ffmpeg >/dev/null 2>&1 || { echo "ffmpeg is required" >&2; exit 1; }

if [[ ! -d "$COMFYUI_DIR/.git" ]]; then
  mkdir -p "$(dirname "$COMFYUI_DIR")"
  git clone --depth 1 https://github.com/Comfy-Org/ComfyUI.git "$COMFYUI_DIR"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r "$COMFYUI_DIR/requirements.txt"
"$PYTHON_BIN" -m pip install "huggingface_hub>=0.34,<1.0"

VHS_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI-VideoHelperSuite"
if [[ ! -d "$VHS_DIR/.git" ]]; then
  git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git "$VHS_DIR"
fi
"$PYTHON_BIN" -m pip install -r "$VHS_DIR/requirements.txt"

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is required after accepting the SDXL and SVD repository terms." >&2
  exit 1
fi

export COMFYUI_DIR HF_TOKEN
"$PYTHON_BIN" - <<'PY'
import os
from pathlib import Path

from huggingface_hub import hf_hub_download

root = Path(os.environ["COMFYUI_DIR"]).resolve()
checkpoints = root / "models" / "checkpoints"
checkpoints.mkdir(parents=True, exist_ok=True)
token = os.environ["HF_TOKEN"]
models = [
    (
        "stabilityai/stable-diffusion-xl-base-1.0",
        "sd_xl_base_1.0.safetensors",
    ),
    (
        "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
        "svd_xt_1_1.safetensors",
    ),
]
for repo_id, filename in models:
    destination = checkpoints / filename
    if destination.is_file() and destination.stat().st_size > 1_000_000:
        print(f"Using existing model: {destination}")
        continue
    print(f"Downloading {repo_id}/{filename}")
    downloaded = Path(
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            token=token,
            local_dir=checkpoints,
        )
    )
    if downloaded.resolve() != destination.resolve():
        downloaded.replace(destination)
PY

echo "Starting ComfyUI on port $COMFYUI_PORT"
cd "$COMFYUI_DIR"
exec "$PYTHON_BIN" main.py \
  --listen 0.0.0.0 \
  --port "$COMFYUI_PORT" \
  --lowvram \
  ${COMFYUI_EXTRA_ARGS:-}
