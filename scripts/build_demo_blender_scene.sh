#!/usr/bin/env bash
set -euo pipefail

BLENDER_BINARY="${BLENDER_BINARY:-blender}"
OUTPUT_PATH="${1:-$PWD/output/blender/workshop_of_light.blend}"

mkdir -p "$(dirname "$OUTPUT_PATH")"

"$BLENDER_BINARY" \
  --background \
  --factory-startup \
  --python workers/blender/bootstrap_workshop.py \
  -- \
  --output "$OUTPUT_PATH"

if [[ ! -s "$OUTPUT_PATH" ]]; then
  echo "Blender workshop scene was not created: $OUTPUT_PATH" >&2
  exit 1
fi

"$BLENDER_BINARY" \
  --background "$OUTPUT_PATH" \
  --python workers/blender/validate_scene.py

printf 'Workshop scene ready: %s (%s bytes)\n' "$OUTPUT_PATH" "$(stat -c%s "$OUTPUT_PATH")"
