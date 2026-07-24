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
  api/              FastAPI control plane and REST API
  web/              Next.js production dashboard
packages/
  agents/           Story, direction, continuity, and quality agents
  engines/          Provider-independent media production engines
  pipeline/         Episode workflow and shared production models
  contracts/        Cross-service schemas
infrastructure/     Database and deployment assets
docs/               Architecture and product decisions
storage/            Local source assets (ignored)
renders/            Generated outputs (ignored)
```

## Local development

```bash
cp .env.example .env
docker compose up --build
```

- Dashboard: `http://localhost:3000`
- API: `http://localhost:8000`
- API health: `http://localhost:8000/api/v1/health`

## Design principles

- A series is a long-lived production entity, not a collection of unrelated videos.
- Character, voice, wardrobe, world, and story continuity are first-class data.
- AI providers are replaceable adapters; business logic must not depend on one vendor.
- Every generation step is reviewable, repeatable, and cost-tracked.
- Failed shots are regenerated independently instead of rebuilding an entire episode.
- Human approval is required before final export and publishing.

## Current foundation

The initial commit provides the monorepo architecture, API health endpoint, production domain models, provider interfaces, orchestration skeleton, dashboard shell, Docker services, and CI checks. Provider integrations and the first full episode workflow come next.
