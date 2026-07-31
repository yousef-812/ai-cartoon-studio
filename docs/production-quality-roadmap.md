# Production Quality Execution Roadmap

> Active branch: `agent/series-bible-foundation`
>
> Product goal: turn the validated AI-cartoon production pipeline into a genuinely watchable, emotionally readable, repeatable cartoon studio.
>
> Update rule: every production-quality code or asset change must update this roadmap in the same commit or in the immediately following roadmap-only commit. The progress ledger is the source of truth for what is actually implemented, not what is merely planned.

## 1. North-star outcome

The system must generate an episode that an uninformed viewer can enjoy without knowing that the pipeline, Blender automation, TTS, or AI systems exist.

The target experience is:

- clear story beats and visual cause-and-effect;
- appealing and recognizable permanent characters;
- readable acting, eye lines, reactions, gestures, and facial expressions;
- deliberate framing and motivated camera movement;
- lighting and effects that support the story;
- character-specific voice identity and emotional delivery;
- synchronized mouth movement and dialogue timing;
- ambience, effects, music, and a balanced final mix;
- continuity across shots and episodes;
- deterministic, retryable automation rather than repeated manual scene editing.

A technically valid MP4 is not a successful result. Passing media probes is a delivery requirement, not the quality bar.

## 2. Current baseline

### Completed technical foundation

- [x] Structured Series Bible, story, screenplay, direction, and review gates.
- [x] Persistent Blender workshop scene with registered rigs, anchors, cameras, props, and reusable actions.
- [x] Directed-shot to Blender-manifest conversion.
- [x] Variable shot durations sourced from direction and extended when generated dialogue is longer.
- [x] Variable character counts per shot.
- [x] Automatic hiding of characters not listed in a shot manifest.
- [x] Piper-based Arabic dialogue generation with permanent voice profiles.
- [x] WAV normalization and dialogue placement in Blender renders.
- [x] Timed viseme fallback and MP4 audio output.
- [x] Ordered multi-shot preview assembly with duration and stream reports.
- [x] Framing fixes using registered character anchors.
- [x] Validated timed-cue fields in Blender shot manifests.
- [x] Shot-keyed Golden Scene timeline overrides.
- [x] Headless Blender handlers for flicker, light energy, and camera push cues.

### Baseline quality limitations

- [ ] Placeholder character models are not production-quality assets.
- [ ] Facial expressions are minimal and not emotionally convincing.
- [ ] Body acting is mostly a single full-shot action (`Talk`, `Listen`, etc.).
- [ ] Story events outside the first Golden Scene timeline are not consistently performed visually.
- [ ] Lighting outside timed Golden Scene cues remains mostly static.
- [ ] Camera movement currently supports the first deterministic push cue only.
- [ ] Rain, thunder, spark, prop state, expression, and layered body cues are not yet implemented.
- [ ] Piper voices are stable but still require stronger acting direction or a higher-quality provider.
- [ ] Lip sync is phoneme-estimated rather than forced-aligned.
- [ ] Sound design and music are not yet present in the Blender preview path.
- [ ] No automated visual-interest or acting-quality gate exists.

## 3. Status legend

- `DONE`: implemented, validated, and retained in the production path.
- `IN PROGRESS`: implementation has started and has an executable artifact, but acceptance is incomplete.
- `READY`: requirements and dependencies are complete; work can begin.
- `BLOCKED`: a named dependency is missing.
- `PLANNED`: accepted scope but not yet ready.
- `DEFERRED`: intentionally postponed with a reason.

## 4. Golden Scene strategy

Quality will be developed through one **Golden Scene** before scaling to the full episode.

The first Golden Scene is the opening of **مصباح العاصفة**:

1. the workshop light flickers;
2. the emergency lamp fails;
3. Omar reacts and says: `انطفأ الضوء!`;
4. Nader notices the storm, returns attention to the lamp, and says: `العاصفة تشتد.`;
5. the scene must feel like a story event, not two static talking shots.

The first approved Golden Scene becomes the reference for character quality, acting density, camera grammar, lighting, sound, and automated quality checks.

The committed quality contract is:

- `demo/first-real-episode/golden-scene/spec.json`

The first committed timed event plan is:

- `demo/first-real-episode/golden-scene/timeline.json`

## 5. Dependency graph

```text
M0 Baseline and quality contract
  -> M1 Timed performance/event runtime
      -> M2 Golden Scene lighting and camera performance
      -> M3 Character visual upgrade
          -> M4 Facial rig and emotional acting
          -> M5 Body acting and motion layering
              -> M6 Voice direction and forced alignment
                  -> M7 Sound design and final mix
                      -> M8 Golden Scene approval
                          -> M9 Full episode scaling
                              -> M10 Automated QC and regression gates
                                  -> M11 Production dashboard and release operations
```

Some work can proceed in parallel, but full-episode production approval is blocked until M8.

---

# Milestones

## M0 — Baseline, quality contract, and review evidence

**Status:** `IN PROGRESS`

### Purpose

Create objective evidence for every visual-quality iteration and prevent technically successful but visibly poor results from being promoted.

### Tasks

- [x] Preserve the voiced preview and media reports as the technical baseline.
- [x] Record that the current output is previs/prototype, not release-quality animation.
- [x] Add a Golden Scene specification with beats, framing intent, lighting states, audio events, emotional intent, and hard failures.
- [x] Include human-review questions covering story clarity, acting, framing, audio, and desire to continue watching in the Golden Scene spec.
- [ ] Add a review record schema with reviewer decision, blocking notes, screenshots, artifact versions, and checksums.
- [ ] Generate consistent contact sheets at defined timestamps for every Golden Scene iteration.
- [ ] Prevent rejected Golden Scene outputs from being promoted as approved artifacts.

### Acceptance criteria

- Every Golden Scene run produces video, media report, contact sheet, and review record.
- Review can fail even when rendering, FFmpeg, and media probes succeed.
- A rejected version cannot be marked production-approved.

### Artifacts

- [x] `demo/first-real-episode/golden-scene/spec.json`
- [ ] `output/golden-scene/review.json`
- [ ] `output/golden-scene/contact-sheet.png`

---

## M1 — Timed performance and event runtime

**Status:** `IN PROGRESS` — code complete for first cue set; Lightning render validation pending

### Purpose

Replace static one-action shots with an explicit timeline of story events.

### Implemented cue types

- `light_flicker`: deterministic energy multipliers distributed through a timed window.
- `light_energy`: deterministic light-energy state change.
- `camera_push`: deterministic camera movement along its current viewing direction, with a required focus-object reference.

### Planned cue families

- lighting color and temperature transitions;
- camera pull, pan, tilt, rack focus, and hold;
- character look targets and timed head turns;
- expression changes and blink cues;
- layered body-action segments;
- prop visibility and prop-state changes;
- safe spark and simple particle events;
- sound-effect and ambience references;
- intentional pauses and reaction holds.

### Tasks

- [x] Add validated timeline-cue models to the Blender manifest contract.
- [x] Add a shot-keyed override format for approved performance timelines.
- [x] Load timeline overrides during batch manifest planning.
- [x] Preserve backward compatibility when no timeline override is supplied.
- [x] Include cue counts and override source in generated sequence metadata.
- [x] Implement light-flicker execution.
- [x] Implement light-energy execution.
- [x] Implement camera-push execution.
- [x] Apply cues after camera and character placement.
- [x] Print deterministic cue execution logs.
- [x] Reject unknown cue types and out-of-bounds cue windows.
- [x] Add targeted tests for model validation and manifest injection.
- [x] Add Blender source-contract tests for supported executors.
- [ ] Run targeted compile/tests in Lightning.
- [ ] Render Scene 1 Shots 1–2 with the committed timeline.
- [ ] Review flicker, exposure, camera movement, and face readability.

### Acceptance criteria

- Scene 1 Shot 1 visibly flickers and dims through deterministic keyframes.
- Scene 1 Shot 1 includes a subtle motivated camera push.
- Scene 1 Shot 2 includes a storm-light flash without changing shot duration.
- Replanning the same inputs creates identical timeline manifests.
- Invalid cues fail before Blender starts rendering.
- The cue implementation passes a real Blender render, not only source tests.

### Artifacts

- [x] `demo/first-real-episode/golden-scene/timeline.json`
- [x] Timeline schema in `packages/blender/models.py`
- [x] Batch injection in `packages/blender/batch.py`
- [x] CLI loading in `scripts/plan_demo_blender_sequence.py`
- [x] Blender execution in `workers/blender/shot_executor.py`
- [x] Tests in `apps/api/tests/test_blender_timeline.py`
- [ ] Rendered Golden Scene preview with visible cue execution

---

## M2 — Golden Scene lighting, effects, and camera grammar

**Status:** `IN PROGRESS` — first flicker and push design committed; visual approval pending

### Purpose

Make the opening feel like a storm-driven story event.

### Tasks

- [ ] Establish a reviewed cool storm-night base-lighting state.
- [x] Commit deterministic workshop-light flicker values for Shot 1.
- [x] Commit emergency-lamp failure values for Shot 1.
- [x] Commit a window-side lightning-flash cue for Shot 2.
- [ ] Validate the flash does not overexpose Nader.
- [ ] Add rain motion or a reusable window-rain effect.
- [x] Commit subtle push-in cues motivated by the light failure and Nader response.
- [ ] Add a timed reaction hold after Omar's line.
- [ ] Add Nader eyeline change: window -> lamp -> speaking direction.
- [ ] Define shot-specific lens, headroom, and safe-framing rules.
- [ ] Add render-time checks that the active camera targets the approved focus anchor.
- [ ] Add exposure and face-readability evidence to the Golden Scene report.

### Acceptance criteria

- Muted viewing communicates that the light failed during a storm.
- Both faces remain readable through the light transition.
- Camera movement feels motivated, subtle, and non-procedural.
- No shot contains empty framing, unwanted crop, or unintended character overlap.

---

## M3 — Production character visual upgrade

**Status:** `PLANNED`

### Purpose

Replace placeholder primitives with appealing permanent characters while preserving registry and automation contracts.

### Omar requirements

- recognizable young inventor silhouette;
- teal workshop jacket, cream shirt, dark trousers, practical shoes;
- round glasses as a stable signature feature;
- readable eyes, brows, mouth, and facial planes;
- topology suitable for facial shape keys and deformation.

### Nader requirements

- recognizable younger apprentice silhouette;
- orange hoodie and navy workshop apron;
- more energetic posture than Omar;
- readable eyes, brows, mouth, and facial planes;
- distinct proportions and palette from Omar.

### Tasks

- [ ] Approve turnaround and expression reference sheets.
- [ ] Produce or import production meshes with documented licensing.
- [ ] Preserve `Omar_Rig`, `Nader_Rig`, mouth-object, and registry identities or provide migration tooling.
- [ ] Add glasses, wardrobe details, and signature props.
- [ ] Add skin, fabric, hair, eye, and accent materials.
- [ ] Add LOD or preview-quality variants for fast iteration.
- [ ] Add asset validation for missing materials, scale, origin, and rig binding.

### Acceptance criteria

- Characters are recognizable in silhouette and close-up.
- Character identity remains stable across all shots.
- Replacement assets work with headless rendering and existing manifests.
- No manual relinking is required per shot.

---

## M4 — Facial rig, expressions, eyes, and lip sync

**Status:** `PLANNED`

### Tasks

- [ ] Add brows, eyelids, pupils, eye aim controls, jaw, lips, cheeks, and basic phoneme shapes.
- [ ] Add expression presets: neutral, surprise, worry, focus, relief, smile.
- [ ] Add blink generation with deterministic timing and suppression during critical poses.
- [ ] Add eye saccades and shot-specific look targets.
- [ ] Replace scale-based mouth fallback with facial shape keys.
- [ ] Add Arabic forced alignment and phoneme-to-viseme mapping.
- [ ] Add coarticulation, rests, and emotion modulation.
- [ ] Validate mouth visibility and face orientation during dialogue.

### Acceptance criteria

- Dialogue is understandable with audio muted through mouth rhythm and expression.
- Characters do not stare blankly or blink mechanically.
- Emotional state is visible before or during the line.
- No lip movement continues after dialogue audio ends.

---

## M5 — Body acting and reusable motion layering

**Status:** `PLANNED`

### Tasks

- [ ] Replace placeholder `Surprised` and `Worried` clips with authored motions.
- [ ] Add reaction, settle, listen, think, look, point, reach, recoil, hold, and smile clips.
- [ ] Add NLA-based action layering instead of one action for the entire shot.
- [ ] Support timed action segments and transitions.
- [ ] Add additive head, spine, hand, and breathing layers.
- [ ] Add prop-hand constraints and release timing.
- [ ] Add character-specific motion-style parameters.
- [ ] Add a motion-retargeting contract for external libraries or mocap.

### Acceptance criteria

- Every dialogue shot contains preparation, delivery, and reaction/settle beats.
- Listeners visibly react instead of playing a generic loop.
- No major pose pops occur at action boundaries.
- Motion remains readable at normal playback speed.

---

## M6 — Voice acting quality and dialogue timing

**Status:** `READY` for provider evaluation; forced alignment depends on M4

### Tasks

- [x] Preserve permanent voice profiles per character.
- [x] Generate one independent audio file per screenplay line.
- [x] Normalize dialogue WAV output to 48 kHz mono.
- [ ] Evaluate higher-quality Arabic TTS providers behind the existing adapter.
- [ ] Add acting controls for urgency, restraint, warmth, worry, and relief.
- [ ] Add pronunciation overrides and diacritization support.
- [ ] Add silence trimming while preserving intentional breaths.
- [ ] Add automatic loudness normalization per line.
- [ ] Add forced phoneme-alignment output.
- [ ] Add human voice review and selective regeneration.

### Acceptance criteria

- Omar and Nader are distinguishable without seeing the screen.
- Delivery matches screenplay emotion and action beat.
- Dialogue begins and ends inside the intended performance window.
- Regenerating one line does not change other approved lines.

---

## M7 — Sound design, ambience, and music

**Status:** `PLANNED`

### Tasks

- [ ] Add loopable rain ambience and controlled thunder events.
- [ ] Add workshop room tone.
- [ ] Add lamp flicker, switch, electrical hum, and safe spark effects.
- [ ] Add subtle score with cueable intensity states.
- [ ] Add per-shot cue manifests and deterministic placement.
- [ ] Duck ambience/music under dialogue.
- [ ] Normalize shot and final-master loudness.
- [ ] Preserve licensing evidence and generation metadata.

### Acceptance criteria

- Audio alone communicates storm, workshop, failure, reaction, and recovery.
- Dialogue remains intelligible on phone speakers.
- Effects support visible events and do not lead or lag noticeably.
- The mix has no clipping, sudden gain jumps, or distracting loops.

---

## M8 — Golden Scene quality gate and approval

**Status:** `BLOCKED` by M2–M7

### Required review questions

- Is the story event understandable without explanation?
- Are the characters appealing and recognizable?
- Do they appear to think and react rather than merely move?
- Is every camera choice motivated?
- Are lighting and sound supporting the same dramatic beat?
- Does the viewer want to continue watching?

### Hard acceptance criteria

- Human review result is `approved`.
- No blocking framing, clipping, continuity, audio, or lip-sync issues.
- Media QC passes.
- The scene can be regenerated from committed inputs and registered assets.
- Approved output checksum and asset versions are recorded.

---

## M9 — Scale the approved grammar to the full episode

**Status:** `BLOCKED` by M8

### Tasks

- [ ] Convert all ten directed shots into detailed performance timelines.
- [ ] Implement lamp indicator, loose wire, reach, spark, recoil, warning gesture, stabilization, reconnection, and final glow.
- [ ] Preserve variable durations and variable character counts.
- [ ] Add continuity state for prop position and lighting across shots.
- [ ] Add reaction coverage and editorial pacing.
- [ ] Render low-cost previews before production-quality frames.
- [ ] Review and approve each shot independently.
- [ ] Assemble and review the complete episode.

### Acceptance criteria

- Every planned beat is visibly performed.
- The episode has a clear beginning, escalation, failure, correction, and payoff.
- No shot feels like filler or a repeated talking template.
- Full-episode approval remains separate from Golden Scene approval.

---

## M10 — Automated quality control and regression protection

**Status:** `PLANNED`

### Tasks

- [ ] Camera-target and subject-in-frame checks.
- [ ] Face visibility, headroom, and screen-coverage checks.
- [ ] Character-count and unintended-character checks.
- [ ] Eye-line and dialogue-speaker checks.
- [ ] Mouth activity versus audio-window checks.
- [ ] Frozen-pose and excessive-static-shot detection.
- [ ] Lighting range and over/underexposure checks.
- [ ] Prop-continuity and state-transition checks.
- [ ] Audio stream, loudness, clipping, silence, and synchronization checks.
- [ ] Contact-sheet comparison and approved-reference regression checks.

### Acceptance criteria

- Known framing and visibility failures are caught before human review.
- Quality regression blocks promotion without blocking unrelated development.
- Reports identify the exact shot, frame range, and failed rule.

---

## M11 — Production dashboard, asset review, and release operations

**Status:** `PLANNED`

### Tasks

- [ ] Show Golden Scene and episode milestone status in the dashboard.
- [ ] Review timeline cues, assets, voice lines, and shot outputs independently.
- [ ] Allow retry of one failed cue, voice, effect, or shot.
- [ ] Record approvals, notes, artifact versions, and checksums.
- [ ] Provide low-resolution preview and production render profiles.
- [ ] Generate release manifest, subtitles, thumbnail, title, description, tags, chapters, and credits.
- [ ] Track licenses for models, textures, meshes, motion, music, fonts, and datasets.
- [ ] Keep publishing manual by default until explicitly approved.

---

# Work streams

## Runtime and automation

- manifest schemas;
- timeline planning;
- Blender execution;
- deterministic rendering;
- retry and recovery;
- QC reports.

## Character art

- concept approval;
- modeling;
- topology;
- materials;
- wardrobe;
- rig integration.

## Acting and direction

- performance beats;
- facial poses;
- body motion;
- camera grammar;
- reaction timing;
- editorial pacing.

## Audio

- voice identity;
- acting delivery;
- forced alignment;
- ambience;
- effects;
- music;
- final mix.

## Review and release

- contact sheets;
- human review;
- regression checks;
- artifact versioning;
- licensing;
- final release package.

# Definition of done for any roadmap item

An item can be marked `DONE` only when all applicable conditions hold:

1. implementation is committed on the active branch;
2. schema and error handling are defined;
3. targeted tests or deterministic validation exist;
4. an executable artifact or report demonstrates behavior;
5. documentation and this roadmap are updated;
6. no unrelated GitHub Actions run is triggered merely to record progress;
7. known limitations are written explicitly.

# Execution policy

- Keep PR #1 in Draft until the Golden Scene gate is approved or the user explicitly changes the policy.
- Do not merge automatically.
- Do not render all production shots merely because the pipeline can do so.
- Use two-shot Golden Scene previews while visual quality is changing.
- Reuse generated voice lines unless voice quality itself is under review.
- Prefer code-driven reusable systems over one-off manual Blender edits.
- Preserve the permanent scene-registry contract when replacing assets.
- Heavy GitHub Actions remain manual or Draft-to-Ready only.

# Progress ledger

## 2026-07-30 — Roadmap initialized

- Commits: `917ebe0`, `8e32ce4`
- Added the detailed production-quality execution roadmap and linked it from the product roadmap.
- Classified current output as validated previs, not final animation.
- Set the Golden Scene as the gate for full-episode production.
- Started M0 and M1.

## 2026-07-30 — Golden Scene quality contract

- Commit: `45889be`
- Completed: M0 Golden Scene specification and initial human-review questions.
- Artifact: `demo/first-real-episode/golden-scene/spec.json`
- Validation: JSON/schema validation will run in the targeted Lightning check.
- Known limitation: review-record and contact-sheet automation are not implemented yet.
- Next action: create review schema and contact-sheet generator after the first cue render.

## 2026-07-30 — Timed Blender cue foundation

- Commits: `4a00a33`, `ca294e6`, `f994469`, `d3e72a0`, `e3bc986`, `417d3ea`, `a634423`, `c0b2691`, `db68618`
- Completed code tasks: validated cue models, shot-keyed overrides, batch injection, CLI loading, flicker, light-energy, camera-push execution, deterministic logs, compatibility handling, and targeted tests.
- Artifacts:
  - `demo/first-real-episode/golden-scene/timeline.json`
  - `packages/blender/models.py`
  - `packages/blender/planner.py`
  - `packages/blender/batch.py`
  - `scripts/plan_demo_blender_sequence.py`
  - `workers/blender/shot_executor.py`
  - `apps/api/tests/test_blender_timeline.py`
- Validation: source review completed; local container could not reach GitHub for checkout. Lightning compile, targeted tests, and real Blender render remain required.
- Known limitations: only three cue types are currently supported; no timed character-acting cues or sound-effect cues yet.
- Next action: pull the branch in Lightning, run targeted checks, and render only Scene 1 Shots 1–2 with sound.

## Update template

```markdown
## YYYY-MM-DD — <short milestone update>

- Commit: `<sha>`
- Roadmap items completed: `<IDs or task names>`
- Artifacts: `<paths>`
- Validation: `<commands/results>`
- Known limitations: `<explicit limitations>`
- Next action: `<one concrete next action>`
```
