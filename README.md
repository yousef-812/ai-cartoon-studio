# AI Cartoon Studio

A production-oriented AI system for creating complete, original cartoon episodes: story development, script writing, shot direction, visual generation, animation, voice acting, lip sync, sound design, quality control, and final rendering.

This repository is intentionally structured around the final product direction. It is not a slideshow or motion-comic prototype.

## Core production flow

1. Create a series bible and permanent character identities.
2. Generate and approve an episode story.
3. Generate and approve a timed screenplay with dialogue and emotions.
4. Convert the screenplay into reviewed camera shots.
5. Produce and approve character references, backgrounds, and shot keyframes.
6. Convert approved keyframes into independent animated video clips.
7. Generate and approve permanent character voice lines.
8. Run lip sync and dialogue placement.
9. Generate ambience, effects, music, and approved shot mixes.
10. Run quality control and final rendering.

## Repository layout

```text
apps/
  api/              FastAPI control plane, Celery workers, and REST API
  web/              Next.js production dashboards
packages/
  agents/           Story, script, direction, continuity, and quality agents
  llm/              Self-hosted OpenAI-compatible LLM adapter
  images/           Replaceable local image provider contracts
  videos/           Replaceable local image-to-video provider contracts
  audio/            Replaceable self-hosted speech provider contracts
  stories/          Story schemas, prompts, jobs, and validation
  scripts/          Screenplay and dialogue production
  direction/        Shot breakdown and camera direction
  visuals/          Visual asset manifests and review gates
  animations/       Animated shot planning and review
  voices/           Character voice line planning and review
  sound/            Ambience, effects, music, sound jobs, and review gates
  mixing/           FFmpeg dialogue ducking and loudness-normalized mixing
  artifacts/        Durable local artifact storage
  pipeline/         Episode workflow and shared production models
  contracts/        Cross-service schemas
notebooks/           Colab GPU worker notebook
scripts/             Local and Lightning AI launch scripts
workflows/           Configurable ComfyUI workflows
infrastructure/      Database and deployment assets
docs/                Architecture and production guides
storage/             Generated production assets (ignored)
renders/             Final renders (ignored)
```

## Local development

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: `http://localhost:3000`
- Story and screenplay: `http://localhost:3000/production`
- Direction: `http://localhost:3000/direction`
- Visual assets: `http://localhost:3000/visuals`
- Animated shots: `http://localhost:3000/animations`
- Character voices: `http://localhost:3000/voices`
- Lip sync: `http://localhost:3000/lip-sync`
- Sound design and music: `http://localhost:3000/sound-design`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/api/v1/health`
- Local LLM health: `http://localhost:8000/api/v1/llm/health`
- Image worker health: `http://localhost:8000/api/v1/images/health`
- Video worker health: `http://localhost:8000/api/v1/video/health`
- Voice worker health: `http://localhost:8000/api/v1/voice/health`
- Lip-sync worker health: `http://localhost:8000/api/v1/lip-sync/health`
- Sound system health: `http://localhost:8000/api/v1/sound/health`

Docker starts PostgreSQL, Redis, FastAPI, a Celery production worker, FFmpeg, and the dashboard. Self-hosted LLM, image, video, voice, lip-sync, and sound-generation endpoints run separately on GPU workstations, Lightning AI, Colab, or compatible private hosts.

## Design principles

- A series is a long-lived production entity, not a collection of unrelated videos.
- Character, voice, wardrobe, world, and story continuity are first-class data.
- AI providers are replaceable adapters; business logic must not depend on one vendor.
- Generated provider URLs are temporary; approved files are copied into durable project storage.
- Every generation step is reviewable, repeatable, and independently retryable.
- Human approval is required before downstream production and final publishing.

## Current production API

```text
POST   /api/v1/series
GET    /api/v1/series
POST   /api/v1/series/{series_id}/characters
PATCH  /api/v1/characters/{character_id}

POST   /api/v1/series/{series_id}/story-jobs
POST   /api/v1/story-jobs/{job_id}/review
POST   /api/v1/story-jobs/{job_id}/script-jobs
POST   /api/v1/script-jobs/{job_id}/review
POST   /api/v1/script-jobs/{job_id}/direction-jobs
POST   /api/v1/direction-jobs/{job_id}/review

POST   /api/v1/direction-jobs/{job_id}/visual-assets/plan
POST   /api/v1/visual-assets/{asset_id}/generate
POST   /api/v1/visual-assets/{asset_id}/review

POST   /api/v1/direction-jobs/{job_id}/animation-jobs/plan
POST   /api/v1/animation-jobs/{job_id}/retry
POST   /api/v1/animation-jobs/{job_id}/review

POST   /api/v1/script-jobs/{job_id}/voice-jobs/plan
POST   /api/v1/voice-jobs/{job_id}/retry
POST   /api/v1/voice-jobs/{job_id}/review

POST   /api/v1/direction-jobs/{job_id}/lip-sync-jobs/plan
POST   /api/v1/lip-sync-jobs/{job_id}/retry
POST   /api/v1/lip-sync-jobs/{job_id}/review

POST   /api/v1/direction-jobs/{job_id}/sound-jobs/plan
POST   /api/v1/sound-jobs/{job_id}/retry
POST   /api/v1/sound-jobs/{job_id}/review
```

All generation jobs are persisted before they are sent to temporary GPU workers. A disconnected worker does not erase requests, attempts, generated files, errors, or review decisions.

## Sound design and music

The production pipeline includes permanent shot-level ambience, visible-action effects, and instrumental music generation. Music is automatically ducked during approved dialogue windows, all layers are mixed and loudness-normalized with FFmpeg, and every source asset plus final shot mix is retained under stable `/artifacts/...` URLs.

Dashboard: `/sound-design`

See [`docs/local-llm.md`](docs/local-llm.md), [`docs/visual-production.md`](docs/visual-production.md), [`docs/animation-production.md`](docs/animation-production.md), [`docs/voice-production.md`](docs/voice-production.md), and [`docs/roadmap.md`](docs/roadmap.md).
