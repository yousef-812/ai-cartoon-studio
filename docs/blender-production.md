# Reusable Blender scene production

The primary character-animation path is a reusable Blender scene rather than regenerating every pose as a new image. SDXL and IP-Adapter remain useful for concept art, textures, and design exploration, but they are not the source of truth for frame-to-frame character identity.

## Permanent production assets

A series keeps these assets stable across episodes:

- one `.blend` environment scene per reusable location;
- one rig object per character;
- permanent mesh, materials, wardrobe, and facial controls;
- named anchor objects for blocking;
- named action clips such as idle, talk, listen, point, pick up, and walk;
- named camera presets;
- registered props;
- mouth controls that accept viseme cues.

`demo/first-real-episode/blender/scene_registry.json` is the contract between the control plane and the Blender file. Final character models may replace the procedural placeholders without changing the registered rig, anchor, action, camera, prop, and mouth-control names.

## Shot JSON contract

Every shot is represented by a `BlenderShotManifest` containing:

- exact duration, frame rate, resolution, render engine, and sample count;
- one registered camera and optional camera movement;
- registered characters, anchors, actions, emotions, and eye-line targets;
- optional dialogue audio and time-based viseme cues;
- registered props and optional hand-bone parenting;
- production metadata and continuity notes.

The headless executor is `workers/blender/shot_executor.py`. It opens the permanent scene, applies the manifest, adds optional dialogue audio, animates mouth controls, and renders one MP4. It never generates a new character design.

## Demo scene

The repository contains a procedural bootstrap scene so the pipeline can be tested before final art assets exist. It creates:

- a consistent workshop with walls, floor, workbench, shelf, storm window, lantern, and tools;
- warm key light, cool fill light, and lantern glow;
- wide, medium, and close camera presets;
- permanent blocking anchors;
- placeholder Omar and Nader armatures;
- reusable body actions;
- mouth objects that receive viseme animation.

Build the scene:

```bash
bash scripts/setup_demo_blender.sh
bash scripts/build_demo_blender_scene.sh
```

Render the first two-character interaction:

```bash
bash scripts/render_demo_blender_shot.sh
```

Expected outputs:

```text
output/blender/workshop_of_light.blend
output/blender/shot_smoke.mp4
```

## API provider

Set these values on the worker that has Blender installed:

```env
VIDEO_PROVIDER=local-blender
BLENDER_BINARY=blender
BLENDER_RUNNER_SCRIPT=/workspace/workers/blender/shot_executor.py
BLENDER_JOBS_PATH=/workspace/renders/blender-jobs
BLENDER_TIMEOUT_SECONDS=1800
```

Create animation jobs with `engine=blender`, a permanent scene path, and its registry path. The planner uses the approved environment concept as the human-review gate, then produces one Blender manifest per directed shot. The legacy `image_to_video` engine remains available for special effects and non-character shots.

## Dialogue and lip sync

The Blender manifest accepts the approved voice file, start time, duration, and viseme timeline for each speaking character. The included Arabic-friendly viseme builder is a deterministic fallback. A future forced-alignment provider can replace the viseme builder without changing the Blender scene, worker, API, or shot-manifest schema.

For final production, voice generation should finish before the final Blender dialogue render. Silent blocking and camera previews may render earlier. This avoids rendering a body-animation clip and then trying to repair identity or mouth motion in a separate generative-video pass.

## Replacement rules

A final model is accepted only when it preserves the registry contract:

- rig object name;
- required bone names;
- mouth object or `viseme_*` shape keys;
- action names;
- scale and forward-axis convention;
- anchor compatibility.

This allows character art to improve without rebuilding the directing, planning, rendering, audio, sound, or finalization systems.
