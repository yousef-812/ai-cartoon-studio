# AI Cartoon Studio

A production-oriented AI system for creating complete, original cartoon episodes: story development, script writing, shot direction, visual generation, animation, voice acting, lip sync, sound design, quality control, and final rendering.

This repository is intentionally structured around the final product direction. It is not a slideshow or motion-comic prototype.

## Core production flow

1. Create a series bible and permanent character identities.
2. Generate an episode premise, story, script, and dialogue.
3. Convert the script into scenes and camera shots.
4. Produce consistent visual assets and animated shots.
5. Generate character voices, emotions, and lip sync.
6. Add sound design and music with commercial-use rights.
7. Run continuity and quality checks.
8. Render a reviewable episode, thumbnail, subtitles, and Shorts candidates.

## Repository layout

```text
apps/
  api/              FastAPI control plane, Celery worker, and REST API
  web/              Next.js production dashboard
packages/
  agents/           Story, direction, continuity, and quality agents
  llm/              Self-hosted OpenAI-compatible LLM adapter
  stories/          Story schemas, prompts, jobs, and validation
  engines/          Provider-independent media production engines
  pipeline/         Episode workflow and shared production models
  contracts/        Cross-service schemas
notebooks/           Colab GPU worker notebook
scripts/             Local and Lightning AI launch scripts
infrastructure/      Database and deployment assets
docs/                Architecture and product decisions
storage/             Local source assets (ignored)
renders/             Generated outputs (ignored)
```

## Local development

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/api/v1/health`
- Local LLM health: `http://localhost:8000/api/v1/llm/health`

Docker starts PostgreSQL, Redis, FastAPI, a Celery production worker, and the dashboard. The self-hosted LLM endpoint runs separately on a GPU workstation, Lightning AI, Colab, or another compatible host.

## Design principles

- A series is a long-lived production entity, not a collection of unrelated videos.
- Character, voice, wardrobe, world, and story continuity are first-class data.
- AI providers are replaceable adapters; business logic must not depend on one vendor.
- The language model is self-hosted and accessed through an OpenAI-compatible protocol.
- Every generation step is reviewable, repeatable, and cost-tracked.
- Failed jobs and shots are retried independently instead of rebuilding an entire episode.
- Human approval is required before final export and publishing.

## Series Bible API

```text
POST   /api/v1/series
GET    /api/v1/series
GET    /api/v1/series/{series_id}
PATCH  /api/v1/series/{series_id}
POST   /api/v1/series/{series_id}/locations
GET    /api/v1/series/{series_id}/locations
POST   /api/v1/series/{series_id}/characters
GET    /api/v1/series/{series_id}/characters
GET    /api/v1/characters/{character_id}
PATCH  /api/v1/characters/{character_id}
```

## Local story engine

```text
GET    /api/v1/llm/health
POST   /api/v1/series/{series_id}/story-jobs
GET    /api/v1/series/{series_id}/story-jobs
GET    /api/v1/story-jobs/{job_id}
POST   /api/v1/story-jobs/{job_id}/retry
```

Story jobs are persisted before they are sent to the GPU worker. If a free GPU session stops, the request, attempts, result, and error remain in PostgreSQL and can be retried later.

See [`docs/local-llm.md`](docs/local-llm.md), [`docs/roadmap.md`](docs/roadmap.md), and [`notebooks/local_llm_colab.ipynb`](notebooks/local_llm_colab.ipynb).
