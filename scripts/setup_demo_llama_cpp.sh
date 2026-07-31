#!/usr/bin/env bash
set -euo pipefail

LLAMA_CPP_DIR="${LLAMA_CPP_DIR:-$PWD/.runtime/llama.cpp}"
BUILD_JOBS="${BUILD_JOBS:-$(nproc 2>/dev/null || echo 4)}"

command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 1; }
command -v cmake >/dev/null 2>&1 || { echo "cmake is required" >&2; exit 1; }
command -v nvcc >/dev/null 2>&1 || {
  echo "CUDA nvcc is required for the GPU build. Use a CUDA runtime image or install the toolkit." >&2
  exit 1
}

if [[ ! -d "$LLAMA_CPP_DIR/.git" ]]; then
  mkdir -p "$(dirname "$LLAMA_CPP_DIR")"
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "$LLAMA_CPP_DIR"
fi

cmake -S "$LLAMA_CPP_DIR" -B "$LLAMA_CPP_DIR/build" \
  -DGGML_CUDA=ON \
  -DLLAMA_CURL=ON \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "$LLAMA_CPP_DIR/build" --config Release --parallel "$BUILD_JOBS"

SERVER="$LLAMA_CPP_DIR/build/bin/llama-server"
if [[ ! -x "$SERVER" ]]; then
  echo "Build completed but llama-server was not found at $SERVER" >&2
  exit 1
fi

echo "llama.cpp is ready: $SERVER"
echo "Start Qwen with:"
echo "LLAMA_SERVER_BIN='$SERVER' bash scripts/start_demo_llm.sh"
