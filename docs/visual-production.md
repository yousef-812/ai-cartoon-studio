# Local visual production

AI Cartoon Studio uses a provider-independent visual asset registry. The first implemented provider is a self-hosted ComfyUI endpoint, which can run on a local GPU, Lightning AI, Colab, or a dedicated GPU server.

## Production order

1. Approve the direction and shot plan.
2. Create the visual asset manifest.
3. Generate permanent character references and master backgrounds.
4. Review and approve those references.
5. Queue dependent expression sheets and shot keyframes.
6. Review each keyframe before animation.

The API enforces dependencies. A shot keyframe cannot be queued while one of its required references is missing or unapproved.

## Configuration

```env
IMAGE_PROVIDER=local-comfyui
IMAGE_BASE_URL=https://your-comfyui-endpoint
IMAGE_WORKFLOW_PATH=/workspace/workflows/comfyui/sdxl.json
IMAGE_CLIENT_ID=ai-cartoon-studio
IMAGE_TIMEOUT_SECONDS=600
IMAGE_POLL_INTERVAL_SECONDS=2
```

The repository includes `workflows/comfyui/sdxl.json`. It contains:

- A normal ComfyUI API workflow.
- A separate `bindings` map that identifies where prompt, negative prompt, width, height, seed, steps, and guidance should be injected.

The workflow can be replaced without changing the asset planner, database, API, dashboard, or worker code.

## Model requirement

The included example workflow references:

```text
sd_xl_base_1.0.safetensors
```

Install that checkpoint in ComfyUI or replace the checkpoint name in the workflow with an available model. Later character-consistency workflows can add LoRA, IP-Adapter, ControlNet, pose conditioning, and approved reference images.

## API flow

```text
GET  /api/v1/images/health
POST /api/v1/direction-jobs/{id}/visual-assets/plan
GET  /api/v1/series/{id}/visual-assets
GET  /api/v1/visual-assets/{id}
POST /api/v1/visual-assets/{id}/queue
POST /api/v1/visual-assets/{id}/retry
POST /api/v1/visual-assets/{id}/review
```

The dashboard is available at `/visuals`.

## Data retained for every asset

- Permanent asset key and type.
- Series and approved direction source.
- Scene and shot numbers when applicable.
- Prompt, negative prompt, size, seed, steps, guidance, and metadata.
- Dependency keys.
- Provider and provider job ID.
- Attempt count, errors, timestamps, and generated image records.
- Human review status and notes.

Provider URLs may be temporary. Durable storage download and checksum tracking are part of the next production phase.
