# Product roadmap

This roadmap preserves one final direction: a complete AI cartoon production studio. Each phase adds permanent production capability rather than creating a disposable prototype.

## Completed production foundation

- Monorepo, FastAPI control plane, Next.js dashboard, Docker, PostgreSQL, Redis, Celery, and CI.
- Persistent series bibles, world rules, locations, characters, visual identities, wardrobes, and voice profiles.
- Self-hosted OpenAI-compatible LLM adapter for vLLM and llama.cpp.
- Lightning AI launcher and Google Colab GPU notebook.
- Persistent generation jobs with retries, validation, status tracking, and human review gates.

## Completed production pipeline

### 1. Story engine

- Generate structured episode stories grounded in the selected series bible.
- Validate characters, locations, continuity, safety rules, scene order, and target duration.
- Require human story approval before screenplay generation.

### 2. Script and dialogue engine

- Convert an approved story into production scenes, action, dialogue, emotions, delivery, pauses, and timing.
- Enforce exact permanent character names and distinct speaking identities.
- Require screenplay approval before directing.

### 3. Director and shot breakdown engine

- Convert an approved screenplay into individual timed shots.
- Define framing, angle, camera movement, composition, visible action, emotion, transitions, and continuity requirements.
- Guarantee that every screenplay dialogue line is assigned to a shot.
- Require shot-plan approval before visual production.

### 4. Visual asset foundation

- Create deterministic manifests for character references, expression sheets, master backgrounds, and shot keyframes.
- Use a replaceable self-hosted ComfyUI provider with configurable workflow bindings.
- Persist prompts, seeds, provider job IDs, results, retries, dependencies, and review decisions.
- Block shot keyframes until their required character references and backgrounds are approved.
- Copy generated images into durable project storage and serve stable `/artifacts` URLs.

### 5. Animated shot foundation

- Convert approved, permanently stored keyframes and shot plans into independent video jobs.
- Upload keyframes to replaceable local ComfyUI video workflows and extract MP4 outputs.
- Preserve exact shot duration, frame rate, motion strength, camera direction, and continuity prompts.
- Copy generated clips into durable project storage with MIME type, size, and SHA-256 checksum.
- Review or retry each failed shot independently without rebuilding upstream stages.

### 6. Voice acting foundation

- Store a permanent provider, voice ID, language, description, speed, and pitch for every speaking character.
- Convert every approved screenplay dialogue line into an independent emotion-aware voice job.
- Send text, character voice, language, emotion, delivery, speed, pitch, format, and timing to a replaceable self-hosted TTS endpoint.
- Copy generated audio into durable project storage with MIME type, size, duration metadata, and SHA-256 checksum.
- Review or retry one line independently without regenerating the screenplay or other production stages.

### 7. Lip sync and dialogue placement foundation

- Match approved dialogue lines to the directed shots that cover their screenplay orders.
- Build a non-overlapping timeline with lead-in, exact voice duration, pauses, minimum gaps, and tail padding.
- Support multiple speaking characters in one shot through a single multi-segment manifest.
- Run a replaceable self-hosted MuseTalk, Wav2Lip, LatentSync, ComfyUI, or compatible HTTP wrapper.
- Reject dialogue that exceeds shot duration instead of silently truncating or compressing it.
- Store final lip-synced shots permanently with stable URLs, MIME type, byte size, duration, and SHA-256 checksum.
- Review or retry lip sync independently without rebuilding animation or voice acting.

### 8. Sound design and music

- Select approved lip-synced video for speaking shots and approved animation for silent shots.
- Generate permanent ambience, visible-action effects, and instrumental music through a replaceable self-hosted endpoint.
- Build a deterministic cue timeline with gain, fades, looping, and shot metadata.
- Duck music during dialogue windows and normalize the final mix to a target LUFS value with FFmpeg.
- Store every source sound and mixed shot permanently with checksums and human review gates.

### 9. Quality control and final episode assembly

- Require one successful and approved sound mix for every directed shot.
- Validate stored files, video and audio streams, shot duration, excessive silence, clipping risk, and integrated loudness.
- Recheck the final master after concatenation and loudness normalization.
- Generate SRT and VTT subtitles from approved dialogue placement.
- Produce a permanent episode master, JSON quality report, thumbnail, and vertical Shorts candidates.
- Require final human approval before manual publishing.

## Next production improvements

### 10. Advanced character consistency and animated-shot quality

- Add pose sheets, LoRA/IP-Adapter reference workflows, and identity similarity checks.
- Add automated flicker, face-drift, costume-drift, background-drift, and motion-quality checks.
- Track model, checkpoint, LoRA, ControlNet, and commercial-use metadata for every visual asset.

### 11. Delivery and publishing operations

- Add title, description, tags, chapter, and credits packages for each export.
- Track music, sound, font, model, and dataset licensing evidence for release readiness.
- Add platform-specific export profiles without automatic publishing by default.
- Maintain an immutable release manifest for every approved episode version.
