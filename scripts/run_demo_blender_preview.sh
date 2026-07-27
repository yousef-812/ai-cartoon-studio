#!/usr/bin/env bash
set -euo pipefail

PYTHON_BINARY="${PYTHON_BINARY:-python3}"
PREVIEW_LIMIT="${PREVIEW_LIMIT:-3}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required but was not found" >&2
  exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffprobe is required but was not found" >&2
  exit 1
fi
if ! [[ "$PREVIEW_LIMIT" =~ ^[0-9]+$ ]]; then
  echo "PREVIEW_LIMIT must be a non-negative integer: $PREVIEW_LIMIT" >&2
  exit 1
fi

"$PYTHON_BINARY" -m compileall -q \
  packages/blender/preview.py \
  scripts/build_demo_blender_preview.py

if "$PYTHON_BINARY" -m pytest --version >/dev/null 2>&1; then
  "$PYTHON_BINARY" -m pytest apps/api/tests/test_blender_preview.py -q
else
  echo "pytest is not installed; targeted tests skipped after compile validation."
fi

rm -f \
  output/blender/sequence_preview.mp4 \
  output/blender/sequence_preview.concat.txt \
  output/blender/sequence_preview_report.json

"$PYTHON_BINARY" scripts/build_demo_blender_preview.py --limit "$PREVIEW_LIMIT"

printf '\nBLENDER_PREVIEW_RUN_SUCCEEDED=%s\n' "$PWD/output/blender/sequence_preview.mp4"
ls -lh \
  output/blender/sequence_preview.mp4 \
  output/blender/sequence_preview_report.json \
  output/blender/sequence_preview.concat.txt
