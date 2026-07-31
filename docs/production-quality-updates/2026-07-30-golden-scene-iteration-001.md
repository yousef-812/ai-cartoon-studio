# Golden Scene roadmap update — iteration 001

Date: 2026-07-30

## Validation result

The first committed timed-cue Golden Scene was rendered in Lightning using Scene 1 Shots 1 and 2.

Technical result: **passed**.

- preview status: `preview_succeeded`;
- selected shots: 2 of 10;
- expected duration: 8.0 seconds;
- actual duration: 8.042333 seconds;
- resolution: 1280 x 720;
- frame rate: 24 fps;
- audio: AAC, 48 kHz, stereo;
- both shot-duration checks passed.

Visual review result: **revision required**.

## Roadmap status changes

### M0 — Baseline, quality contract, and review evidence

- First structured human review record added:
  - `demo/first-real-episode/golden-scene/reviews/iteration-001.json`
- The output is explicitly blocked from production approval even though media QC passed.
- M0 remains `IN PROGRESS` until contact-sheet generation and approval-state enforcement are automated.

### M1 — Timed performance and event runtime

The original cue set is now validated in a real Blender render:

- `light_flicker`: visually confirmed;
- `light_energy`: visually confirmed;
- `camera_push`: visually confirmed;
- MP4 audio and variable shot timing remained intact.

M1 remains `IN PROGRESS` because character-performance cues are now being added rather than closing the runtime at the lighting/camera-only level.

### M2 — Golden Scene lighting, effects, and camera grammar

Validated:

- the workshop light visibly flickers;
- the lantern reaches an off/failed state;
- the camera push does not create empty framing;
- Nader remains centered in Shot 2.

Still blocking:

- Nader does not perform the required window -> lamp -> speaking-direction eye line;
- Omar does not perform an authored reaction/settle beat;
- there is no rain, thunder, room tone, or lamp-failure sound design;
- placeholder character art and generic Talk/Listen acting remain below the entertainment bar.

## Implementation started after review

A new validated cue type, `character_look`, has been added to the timeline contract and Blender executor.

The Shot 2 timeline now directs Nader through three deterministic targets:

1. `ENV_WindowGlass`;
2. `PROP_Lantern`;
3. `CAM_Medium`.

The implementation clamps maximum yaw, rejects invalid targets before rendering, emits deterministic execution logs, and has targeted source/schema tests.

## Commits

- `fbb2115` — add validated `character_look` cue contract;
- `6cb88c3` — execute timed character eye lines in Blender;
- `b6e4d17` — direct Nader window/lamp/speaking eye-line beats;
- `0d7e02e` — test character-look injection and validation;
- `0b2740a` — record the first structured Golden Scene review.

## Next validation

Re-render only Scene 1 Shots 1 and 2 and confirm:

- three `TIMELINE_CUE=character_look` log entries appear for Nader;
- Nader visibly turns toward the window, returns to the lantern, and settles toward the speaking direction;
- the camera push remains stable;
- audio and the 8-second variable-duration preview remain valid.

The Golden Scene remains unapproved until the acting, sound, and character-quality blockers are resolved.
