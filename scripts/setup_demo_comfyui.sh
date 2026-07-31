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

IPADAPTER_DIR="$COMFYUI_DIR/custom_nodes/comfyui-ipadapter"
if [[ ! -d "$IPADAPTER_DIR/.git" ]]; then
  git clone --depth 1 https://github.com/comfyorg/comfyui-ipadapter.git "$IPADAPTER_DIR"
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is required after accepting the SDXL and SVD repository terms." >&2
  exit 1
fi

export COMFYUI_DIR HF_TOKEN
"$PYTHON_BIN" - <<'PY'
import os
import shutil
from pathlib import Path

from huggingface_hub import hf_hub_download

root = Path(os.environ["COMFYUI_DIR"]).resolve()
token = os.environ["HF_TOKEN"]

downloads = [
    (
        "stabilityai/stable-diffusion-xl-base-1.0",
        "sd_xl_base_1.0.safetensors",
        root / "models" / "checkpoints" / "sd_xl_base_1.0.safetensors",
    ),
    (
        "stabilityai/stable-video-diffusion-img2vid-xt-1-1",
        "svd_xt_1_1.safetensors",
        root / "models" / "checkpoints" / "svd_xt_1_1.safetensors",
    ),
    (
        "h94/IP-Adapter",
        "models/image_encoder/model.safetensors",
        root
        / "models"
        / "clip_vision"
        / "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
    ),
    (
        "h94/IP-Adapter",
        "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors",
        root / "models" / "ipadapter" / "ip-adapter-plus_sdxl_vit-h.safetensors",
    ),
]

for repo_id, source_filename, destination in downloads:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 1_000_000:
        print(f"Using existing model: {destination}")
        continue
    print(f"Downloading {repo_id}/{source_filename}")
    downloaded = Path(
        hf_hub_download(
            repo_id=repo_id,
            filename=source_filename,
            token=token,
        )
    )
    temporary = destination.with_suffix(destination.suffix + ".download")
    shutil.copyfile(downloaded, temporary)
    temporary.replace(destination)
    print(f"Installed model: {destination} ({destination.stat().st_size} bytes)")
PY

echo "Starting ComfyUI on port $COMFYUI_PORT"
cd "$COMFYUI_DIR"
exec "$PYTHON_BIN" main.py \
  --listen 0.0.0.0 \
  --port "$COMFYUI_PORT" \
  --lowvram \
  ${COMFYUI_EXTRA_ARGS:-}
