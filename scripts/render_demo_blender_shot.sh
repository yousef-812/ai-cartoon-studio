#!/usr/bin/env bash
set -euo pipefail

BLENDER_BINARY="${BLENDER_BINARY:-blender}"
SCENE_PATH="${1:-$PWD/output/blender/workshop_of_light.blend}"
MANIFEST_PATH="${2:-$PWD/demo/first-real-episode/blender/shot_smoke.json}"
OUTPUT_PATH="${3:-$PWD/output/blender/shot_smoke.mp4}"

if [[ ! -s "$SCENE_PATH" ]]; then
  echo "Blender scene is missing: $SCENE_PATH" >&2
  exit 1
fi
if [[ ! -s "$MANIFEST_PATH" ]]; then
  echo "Shot manifest is missing: $MANIFEST_PATH" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

"$BLENDER_BINARY" \
  --background "$SCENE_PATH" \
  --python workers/blender/shot_executor.py \
  -- \
  --manifest "$MANIFEST_PATH" \
  --output "$OUTPUT_PATH"

if [[ ! -s "$OUTPUT_PATH" ]]; then
  echo "Blender shot was not rendered: $OUTPUT_PATH" >&2
  exit 1
fi

printf 'Rendered Blender shot: %s (%s bytes)\n' "$OUTPUT_PATH" "$(stat -c%s "$OUTPUT_PATH")"
