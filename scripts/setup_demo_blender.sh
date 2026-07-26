#!/usr/bin/env bash
set -euo pipefail

BLENDER_BINARY="${BLENDER_BINARY:-blender}"

if ! command -v "$BLENDER_BINARY" >/dev/null 2>&1; then
  echo "Blender is not installed or BLENDER_BINARY is not configured." >&2
  echo "Install Blender, then rerun with BLENDER_BINARY=/path/to/blender if needed." >&2
  exit 1
fi

"$BLENDER_BINARY" --version | head -n 2

python - <<'PY'
from pathlib import Path

from packages.blender.models import BlenderSceneRegistry, BlenderShotManifest

root = Path.cwd()
registry_path = root / "demo" / "first-real-episode" / "blender" / "scene_registry.json"
shot_path = root / "demo" / "first-real-episode" / "blender" / "shot_smoke.json"

registry = BlenderSceneRegistry.model_validate_json(registry_path.read_text(encoding="utf-8"))
shot = BlenderShotManifest.model_validate_json(shot_path.read_text(encoding="utf-8"))

print(f"Scene registry ready: {registry.scene_name}")
print(f"Registered characters: {', '.join(registry.characters)}")
print(f"Smoke shot ready: {shot.shot_key} ({shot.render.frame_end} frames)")
PY

echo "Blender executable and production manifests are ready."
