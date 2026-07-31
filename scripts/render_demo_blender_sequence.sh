#!/usr/bin/env bash
set -euo pipefail

BLENDER_BINARY="${BLENDER_BINARY:-blender}"
PYTHON_BINARY="${PYTHON_BINARY:-python3}"
SHOT_LIMIT="${SHOT_LIMIT:-3}"
AUDIO_ROOT="${AUDIO_ROOT:-}"
GOLDEN_SCENE_PERFORMANCE="${GOLDEN_SCENE_PERFORMANCE:-1}"

SCENE_PATH="${1:-$PWD/output/blender/workshop_of_light.blend}"
MANIFEST_DIR="${2:-$PWD/output/blender/manifests}"
OUTPUT_DIR="${3:-$PWD/output/blender/sequence}"

if [[ ! -s "$SCENE_PATH" ]]; then
  echo "Blender scene is missing: $SCENE_PATH" >&2
  exit 1
fi
if ! [[ "$SHOT_LIMIT" =~ ^[0-9]+$ ]]; then
  echo "SHOT_LIMIT must be a non-negative integer: $SHOT_LIMIT" >&2
  exit 1
fi
if [[ -n "$AUDIO_ROOT" && ! -d "$AUDIO_ROOT" ]]; then
  echo "Generated voice directory is missing: $AUDIO_ROOT" >&2
  exit 1
fi

PLAN_ARGS=(scripts/plan_demo_blender_sequence.py --output-dir "$MANIFEST_DIR")
if [[ -n "$AUDIO_ROOT" ]]; then
  PLAN_ARGS+=(--audio-root "$AUDIO_ROOT")
fi
"$PYTHON_BINARY" "${PLAN_ARGS[@]}"

if [[ "$GOLDEN_SCENE_PERFORMANCE" == "1" ]]; then
  "$PYTHON_BINARY" scripts/apply_golden_scene_performance.py --manifest-dir "$MANIFEST_DIR"
fi

mkdir -p "$OUTPUT_DIR"
mapfile -t MANIFESTS < <(find "$MANIFEST_DIR" -maxdepth 1 -type f -name 'scene_*_shot_*.json' | sort)
if [[ ${#MANIFESTS[@]} -eq 0 ]]; then
  echo "No Blender shot manifests were planned in: $MANIFEST_DIR" >&2
  exit 1
fi

rendered=0
for manifest in "${MANIFESTS[@]}"; do
  if (( SHOT_LIMIT > 0 && rendered >= SHOT_LIMIT )); then
    break
  fi
  stem="$(basename "$manifest" .json)"
  output="$OUTPUT_DIR/$stem.mp4"
  rm -f "$output" "${output%.mp4}.prepared.blend"
  echo
  echo "===== Rendering $stem ====="
  BLENDER_BINARY="$BLENDER_BINARY" bash scripts/render_demo_blender_shot.sh "$SCENE_PATH" "$manifest" "$output"
  rendered=$((rendered + 1))
done

echo
printf 'BLENDER_SEQUENCE_RENDER_SUCCEEDED=%s\n' "$OUTPUT_DIR"
printf 'Rendered shots: %s of %s\n' "$rendered" "${#MANIFESTS[@]}"
if (( SHOT_LIMIT > 0 && rendered < ${#MANIFESTS[@]} )); then
  printf 'Set SHOT_LIMIT=0 to render all planned shots.\n'
fi
