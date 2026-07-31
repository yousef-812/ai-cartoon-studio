#!/usr/bin/env bash
set -euo pipefail

COMFYUI_DIR="${COMFYUI_DIR:-$PWD/.runtime/ComfyUI}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }

if [[ ! -d "$COMFYUI_DIR/.git" ]]; then
  echo "ComfyUI is not installed at $COMFYUI_DIR" >&2
  exit 1
fi

if [[ -z "${HF_TOKEN:-}" ]]; then
  echo "HF_TOKEN is required to download the IP-Adapter model files." >&2
  exit 1
fi

IPADAPTER_DIR="$COMFYUI_DIR/custom_nodes/comfyui-ipadapter"
if [[ ! -d "$IPADAPTER_DIR/.git" ]]; then
  git clone --depth 1 https://github.com/comfyorg/comfyui-ipadapter.git "$IPADAPTER_DIR"
else
  git -C "$IPADAPTER_DIR" pull --ff-only
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

for path in (
    root / "models" / "clip_vision" / "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors",
    root / "models" / "ipadapter" / "ip-adapter-plus_sdxl_vit-h.safetensors",
):
    if not path.is_file() or path.stat().st_size <= 1_000_000:
        raise SystemExit(f"IP-Adapter model validation failed: {path}")
    print(f"Verified: {path} ({path.stat().st_size} bytes)")
PY

echo "IP-Adapter installation is ready. Restart ComfyUI to load the new nodes."
