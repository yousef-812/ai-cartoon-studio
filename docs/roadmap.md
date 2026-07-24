# Product roadmap

This roadmap preserves one final direction: a complete AI cartoon production studio. Each phase adds permanent production capability rather than creating a disposable prototype.

## Completed foundation

- Monorepo, FastAPI control plane, Next.js dashboard, Docker, PostgreSQL, Redis, Celery, and CI.
- Persistent series bibles, world rules, locations, characters, visual identities, wardrobes, and voice profiles.
- Self-hosted OpenAI-compatible LLM adapter for vLLM and llama.cpp.
- Lightning AI launcher and Google Colab GPU notebook.
- Persistent story generation jobs with retries, validation, status tracking, and dashboard controls.
- Story Agent grounded in series, character, location, safety, and continuity context.

## Next production phases

### 1. Script and dialogue engine

- Convert an approved story into acts, scenes, dialogue, emotions, and timing.
- Preserve each character's speaking style and vocabulary.
- Version scripts and require human approval before direction.

### 2. Director and storyboard engine

- Convert scenes into individual camera shots.
- Define framing, lens, movement, blocking, lighting, action, and continuity references.
- Produce structured shot manifests for visual generation.

### 3. Character and environment asset production

- Generate and approve permanent character turnarounds and expression sheets.
- Create reusable location and prop libraries.
- Track prompts, seeds, model versions, and commercial-use rights.

### 4. Animated shot production

- Route shots to replaceable image and video providers.
- Support local ComfyUI workflows and optional cloud providers.
- Regenerate failed shots independently.

### 5. Voice acting and lip sync

- Assign stable voices to characters.
- Generate emotion-aware dialogue and timing metadata.
- Run lip sync and validate audio/visual alignment.

### 6. Sound design and music

- Generate or select licensed ambience, effects, and music.
- Mix dialogue and music automatically with review controls.

### 7. Quality control and final render

- Detect character drift, visual artifacts, continuity errors, silence, clipping, and timing issues.
- Render the full episode, subtitles, thumbnail, and Shorts candidates.
- Require final human approval before manual publishing.
