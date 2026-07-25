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

## Automatic character-reference guidance

Approved character references are reused automatically. When a dependent expression sheet, pose sheet, or shot keyframe is generated, the visual worker:

1. resolves the asset dependency keys;
2. selects approved character-reference images only;
3. stages those images in ComfyUI through `/upload/image`;
4. switches from the base SDXL workflow to the reference-guided IP-Adapter workflow;
5. injects one or two character references into the workflow before queueing the prompt.

One reference is duplicated into both IP-Adapter input slots. Two-character shots use both approved character images. Background assets remain approval dependencies but are not mixed into the character IP-Adapter embeddings.

## Configuration

```env
IMAGE_PROVIDER=local-comfyui
IMAGE_BASE_URL=https://your-comfyui-endpoint
IMAGE_WORKFLOW_PATH=/workspace/workflows/comfyui/sdxl.json
IMAGE_REFERENCE_WORKFLOW_PATH=/workspace/workflows/comfyui/sdxl_ipadapter.json
IMAGE_CLIENT_ID=ai-cartoon-studio
IMAGE_TIMEOUT_SECONDS=600
IMAGE_POLL_INTERVAL_SECONDS=2
```

The repository includes two SDXL workflows:

- `workflows/comfyui/sdxl.json` for references and other generation without dependencies;
- `workflows/comfyui/sdxl_ipadapter.json` for reference-guided dependent assets.

Each file contains:

- a normal ComfyUI API workflow;
- a separate `bindings` map that identifies where prompt, negative prompt, dimensions, seed, steps, guidance, and reference-image filenames are injected.

The workflows can be replaced without changing the asset planner, database, API, dashboard, or worker code.

## Model requirements

The base workflow references:

```text
sd_xl_base_1.0.safetensors
```

The reference workflow additionally requires:

```text
ComfyUI custom node: comfyorg/comfyui-ipadapter
CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors
ip-adapter-plus_sdxl_vit-h.safetensors
```

`scripts/setup_demo_comfyui.sh` installs the custom node and downloads the required model files. Later pose-specific workflows can add ControlNet or OpenPose conditioning without changing the provider contract.

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

Provider URLs may be temporary. Generated files are copied into durable artifact storage with checksum tracking.
