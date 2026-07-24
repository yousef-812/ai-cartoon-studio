# Product roadmap

This roadmap preserves one final direction: a complete AI cartoon production studio. Each phase adds permanent production capability rather than creating a disposable prototype.

## Completed production foundation

- Monorepo, FastAPI control plane, Next.js dashboard, Docker, PostgreSQL, Redis, Celery, and CI.
- Persistent series bibles, world rules, locations, characters, visual identities, wardrobes, and voice profiles.
- Self-hosted OpenAI-compatible LLM adapter for vLLM and llama.cpp.
- Lightning AI launcher and Google Colab GPU notebook.
- Persistent generation jobs with retries, validation, status tracking, and human review gates.

## Completed pre-production pipeline

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

## Next production phases

### 5. Character consistency workflows

- Add pose sheets, LoRA/IP-Adapter reference workflows, and identity similarity checks.
- Store approved reference images in durable object storage rather than temporary provider URLs.
- Track model, checkpoint, LoRA, ControlNet, and commercial-use metadata for every asset.

### 6. Animated shot production

- Convert approved keyframes and shot plans into animated clips.
- Support replaceable local ComfyUI video workflows and optional cloud providers.
- Track first frame, last frame, motion prompt, duration, frame rate, and regeneration history.
- Regenerate failed shots independently.

### 7. Voice acting and lip sync

- Assign stable self-hosted voices to characters.
- Generate emotion-aware dialogue and exact timing metadata.
- Run lip sync and validate audio/visual alignment.

### 8. Sound design and music

- Generate or select licensed ambience, effects, and music.
- Mix dialogue and music automatically with review controls.

### 9. Quality control and final render

- Detect character drift, visual artifacts, continuity errors, silence, clipping, and timing issues.
- Render the full episode, subtitles, thumbnail, and Shorts candidates.
- Require final human approval before manual publishing.
