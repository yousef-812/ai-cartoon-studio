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
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffmpeg and ffprobe are required for Blender shot audio" >&2
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

AUDIO_STREAM="$(
  ffprobe -v error \
    -select_streams a:0 \
    -show_entries stream=index \
    -of csv=p=0 \
    "$OUTPUT_PATH" | head -n 1
)"
if [[ -z "$AUDIO_STREAM" ]]; then
  DURATION="$(
    ffprobe -v error \
      -show_entries format=duration \
      -of default=noprint_wrappers=1:nokey=1 \
      "$OUTPUT_PATH"
  )"
  TEMP_PATH="${OUTPUT_PATH%.mp4}.with-audio.mp4"
  rm -f "$TEMP_PATH"
  ffmpeg -y -hide_banner -loglevel error \
    -i "$OUTPUT_PATH" \
    -f lavfi -t "$DURATION" \
    -i anullsrc=channel_layout=stereo:sample_rate=48000 \
    -map 0:v:0 \
    -map 1:a:0 \
    -c:v copy \
    -c:a aac \
    -ar 48000 \
    -ac 2 \
    -shortest \
    -movflags +faststart \
    "$TEMP_PATH"
  mv "$TEMP_PATH" "$OUTPUT_PATH"
  echo "SHOT_AUDIO_STREAM=silence"
else
  echo "SHOT_AUDIO_STREAM=dialogue"
fi

printf 'Rendered Blender shot: %s (%s bytes)\n' "$OUTPUT_PATH" "$(stat -c%s "$OUTPUT_PATH")"
