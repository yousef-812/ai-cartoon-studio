#!/usr/bin/env bash
set -euo pipefail

PYTHON_BINARY="${PYTHON_BINARY:-python3}"
BLENDER_BINARY="${BLENDER_BINARY:-$PWD/.runtime/blender}"
PIPER_BASE_URL="${PIPER_BASE_URL:-http://127.0.0.1:8001}"
PIPER_API_KEY="${PIPER_API_KEY:-}"
VOICE_OUTPUT_DIR="${VOICE_OUTPUT_DIR:-$PWD/output/voices}"
SHOT_LIMIT="${SHOT_LIMIT:-2}"
PREVIEW_LIMIT="${PREVIEW_LIMIT:-$SHOT_LIMIT}"
VOICE_FORCE="${VOICE_FORCE:-0}"
PIPER_LOG="${PIPER_LOG:-$PWD/logs/piper-tts.log}"
QUALITY_SCENE_REBUILD="${QUALITY_SCENE_REBUILD:-1}"
GOLDEN_SOUND="${GOLDEN_SOUND:-1}"

mkdir -p "$PWD/logs" "$VOICE_OUTPUT_DIR" "$PWD/output/golden-scene/sound"

bash -n \
  scripts/setup_demo_piper.sh \
  scripts/start_demo_piper.sh \
  scripts/build_demo_blender_scene.sh \
  scripts/render_demo_blender_shot.sh \
  scripts/render_demo_blender_sequence.sh \
  scripts/run_demo_blender_preview.sh
"$PYTHON_BINARY" -m compileall -q \
  packages/blender \
  scripts/generate_demo_voice_lines.py \
  scripts/generate_golden_scene_sound.py \
  scripts/mix_golden_scene_audio.py \
  scripts/build_golden_scene_review.py \
  scripts/apply_golden_scene_performance.py \
  scripts/plan_demo_blender_sequence.py \
  workers/blender

if [[ "$QUALITY_SCENE_REBUILD" == "1" ]]; then
  BLENDER_BINARY="$BLENDER_BINARY" bash scripts/build_demo_blender_scene.sh
fi

piper_ready() {
  "$PYTHON_BINARY" - "$PIPER_BASE_URL" <<'PY' >/dev/null 2>&1
import json
import sys
import urllib.request
base = sys.argv[1].rstrip("/")
with urllib.request.urlopen(f"{base}/health", timeout=5) as response:
    payload = json.loads(response.read().decode("utf-8"))
raise SystemExit(0 if payload.get("available") else 1)
PY
}

STARTED_PIPER=0
PIPER_PID=""
cleanup() {
  if [[ "$STARTED_PIPER" == "1" && -n "$PIPER_PID" ]]; then
    kill "$PIPER_PID" >/dev/null 2>&1 || true
    wait "$PIPER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if ! piper_ready; then
  echo "Piper is not running; preparing the local Arabic voice runtime."
  bash scripts/setup_demo_piper.sh
  PIPER_API_KEY="$PIPER_API_KEY" nohup bash scripts/start_demo_piper.sh >"$PIPER_LOG" 2>&1 &
  PIPER_PID=$!
  STARTED_PIPER=1
  ready=0
  for _ in $(seq 1 60); do
    if piper_ready; then
      ready=1
      break
    fi
    if ! kill -0 "$PIPER_PID" >/dev/null 2>&1; then
      echo "Piper exited before becoming ready. Log:" >&2
      tail -n 80 "$PIPER_LOG" >&2 || true
      exit 1
    fi
    sleep 2
  done
  if [[ "$ready" != "1" ]]; then
    echo "Timed out waiting for Piper. Log:" >&2
    tail -n 80 "$PIPER_LOG" >&2 || true
    exit 1
  fi
fi

VOICE_ARGS=(scripts/generate_demo_voice_lines.py --base-url "$PIPER_BASE_URL" --api-key "$PIPER_API_KEY" --output-dir "$VOICE_OUTPUT_DIR")
if [[ "$VOICE_FORCE" == "1" ]]; then
  VOICE_ARGS+=(--force)
fi
"$PYTHON_BINARY" "${VOICE_ARGS[@]}"

if [[ "$GOLDEN_SOUND" == "1" ]]; then
  "$PYTHON_BINARY" scripts/generate_golden_scene_sound.py
fi

export BLENDER_BINARY
export AUDIO_ROOT="$VOICE_OUTPUT_DIR"
export SHOT_LIMIT
export PREVIEW_LIMIT
export GOLDEN_SCENE_PERFORMANCE=1

rm -rf "$PWD/output/blender/sequence"
rm -f "$PWD/output/blender/sequence_preview.mp4" "$PWD/output/blender/sequence_preview.concat.txt" "$PWD/output/blender/sequence_preview_report.json"

bash scripts/render_demo_blender_sequence.sh

if [[ "$GOLDEN_SOUND" == "1" && "$SHOT_LIMIT" -ge 2 ]]; then
  "$PYTHON_BINARY" scripts/mix_golden_scene_audio.py
fi

bash scripts/run_demo_blender_preview.sh

AUDIO_STREAMS="$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 output/blender/sequence_preview.mp4 | wc -l)"
if [[ "$AUDIO_STREAMS" -lt 1 ]]; then
  echo "The Blender preview was created without an audio stream" >&2
  exit 1
fi

"$PYTHON_BINARY" scripts/build_golden_scene_review.py

printf '\nVOICED_BLENDER_PREVIEW_SUCCEEDED=%s\n' "$PWD/output/blender/sequence_preview.mp4"
printf 'Generated voice lines: %s\n' "$(find "$VOICE_OUTPUT_DIR" -maxdepth 1 -type f -name 'scene_*_line_*.wav' | wc -l)"
printf 'Preview audio streams: %s\n' "$AUDIO_STREAMS"
ls -lh \
  output/blender/sequence_preview.mp4 \
  output/blender/sequence_preview_report.json \
  output/golden-scene/contact-sheet.png \
  output/golden-scene/review.json \
  "$VOICE_OUTPUT_DIR/voice_report.json"
