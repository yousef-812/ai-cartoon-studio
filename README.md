# AI Cartoon Studio

A production-oriented AI system for creating complete, original cartoon episodes: story development, script writing, shot direction, visual generation, animation, voice acting, lip sync, sound design, quality control, and final rendering.

This repository is intentionally structured around the final product direction. It is not a slideshow or motion-comic prototype.

## Implemented production flow

1. Create a persistent series bible and permanent character identities.
2. Generate and review an episode story using a self-hosted LLM.
3. Convert an approved story into a timed screenplay with dialogue, emotions, and delivery.
4. Convert an approved screenplay into camera shots with action, timing, and continuity requirements.
5. Create a visual asset manifest for character references, expression sheets, backgrounds, and shot keyframes.
6. Generate visual assets through a self-hosted ComfyUI endpoint and approve dependencies before downstream production.

## Planned production flow

7. Animate approved shot keyframes.
8. Generate stable character voices and lip sync.
9. Add sound design and music with commercial-use records.
10. Run continuity and quality checks.
11. Render a reviewable episode, thumbnail, subtitles, and Shorts candidates.

## Repository layout

```text
apps/
  api/              FastAPI control plane, Celery workers, and REST API
  web/              Next.js production dashboard
packages/
  agents/           Story, script, direction, continuity, and quality agents
  direction/        Directed scene and shot-plan domain
  images/           Replaceable self-hosted image provider contracts
  llm/              Self-hosted OpenAI-compatible LLM adapter
  scripts/           Screenplay and dialogue domain
  stories/           Story generation domain
  visuals/           Visual asset manifest, dependencies, and review domain
  engines/           Provider-independent media production engines
  pipeline/          Episode workflow and shared production models
  contracts/         Cross-service schemas
workflows/
  comfyui/           Configurable ComfyUI API workflows and bindings
notebooks/            Colab GPU worker notebook
scripts/              Local and Lightning AI launch scripts
infrastructure/       Database and deployment assets
docs/                 Architecture and product decisions
storage/              Local source assets (ignored)
renders/              Generated outputs (ignored)
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
- Local image health: `http://localhost:8000/api/v1/images/health`
- Series Bible: `http://localhost:3000`
- Story and screenplay: `http://localhost:3000/production`
- Direction and shot review: `http://localhost:3000/direction`
- Visual asset production: `http://localhost:3000/visuals`

Docker starts PostgreSQL, Redis, FastAPI, Celery workers, and the dashboard. The self-hosted LLM and ComfyUI endpoints run separately on a GPU workstation, Lightning AI, Colab, or another compatible host.

## Self-hosted inference

```env
LLM_BASE_URL=https://your-vllm-or-llamacpp-endpoint/v1
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct-AWQ
IMAGE_BASE_URL=https://your-comfyui-endpoint
IMAGE_WORKFLOW_PATH=/workspace/workflows/comfyui/sdxl.json
```

Temporary free-GPU sessions can stop without losing production state. PostgreSQL keeps requests, prompts, outputs, errors, review decisions, and retry history.

## Review gates

```text
Series Bible
→ Story review
→ Screenplay review
→ Direction review
→ Character/background reference review
→ Shot keyframe review
→ Animation
```

The API enforces these gates. A downstream job cannot be created from an unapproved upstream result.

## Design principles

- A series is a long-lived production entity, not a collection of unrelated videos.
- Character, voice, wardrobe, world, and story continuity are first-class data.
- AI providers are replaceable adapters; business logic must not depend on one vendor.
- Every generation step is reviewable, repeatable, dependency-aware, and recoverable.
- Failed assets and shots are regenerated independently instead of rebuilding an episode.
- Human approval is required before final export and publishing.

See [`docs/local-llm.md`](docs/local-llm.md), [`docs/visual-production.md`](docs/visual-production.md), [`docs/roadmap.md`](docs/roadmap.md), and [`notebooks/local_llm_colab.ipynb`](notebooks/local_llm_colab.ipynb).
