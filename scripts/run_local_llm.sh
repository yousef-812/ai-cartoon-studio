#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-7B-Instruct-AWQ}"
LLM_API_KEY="${LLM_API_KEY:-change-this-private-token}"
LLM_PORT="${LLM_PORT:-8001}"
VLLM_EXTRA_ARGS="${VLLM_EXTRA_ARGS:-}"

python -m pip install --upgrade "vllm>=0.6"

# shellcheck disable=SC2086
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_ID" \
  --host 0.0.0.0 \
  --port "$LLM_PORT" \
  --api-key "$LLM_API_KEY" \
  --trust-remote-code \
  $VLLM_EXTRA_ARGS
