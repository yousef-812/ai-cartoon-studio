#!/usr/bin/env bash
set -euo pipefail

LLAMA_SERVER_BIN="${LLAMA_SERVER_BIN:-llama-server}"
MODEL="${LLM_MODEL:-Qwen/Qwen3-8B-GGUF:Q4_K_M}"
PORT="${LLM_PORT:-8080}"
CONTEXT="${LLM_CONTEXT_SIZE:-16384}"
GPU_LAYERS="${LLM_GPU_LAYERS:-99}"

if [[ -z "${LLM_API_KEY:-}" ]]; then
  echo "Set LLM_API_KEY before exposing the demo server." >&2
  exit 1
fi
command -v "$LLAMA_SERVER_BIN" >/dev/null 2>&1 || {
  echo "llama-server was not found. Install or build llama.cpp first." >&2
  exit 1
}

exec "$LLAMA_SERVER_BIN" \
  -hf "$MODEL" \
  --host 0.0.0.0 \
  --port "$PORT" \
  --ctx-size "$CONTEXT" \
  --n-gpu-layers "$GPU_LAYERS" \
  --api-key "$LLM_API_KEY" \
  --no-webui \
  --jinja
