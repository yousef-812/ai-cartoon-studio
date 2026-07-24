# Self-hosted animated shot production

AI Cartoon Studio treats animation as a replaceable GPU worker, not as permanent application infrastructure. The API, PostgreSQL records, approved keyframes, generated clips, and review decisions remain in the project even when Lightning AI or Colab disconnects.

## Default ComfyUI workflow

The included `workflows/comfyui/svd.json` is an image-to-video template based on Stable Video Diffusion. It expects:

- a compatible SVD image-only checkpoint such as `svd_xt_1_1.safetensors`;
- the standard ComfyUI SVD nodes;
- VideoHelperSuite for the `VHS_VideoCombine` MP4 output node;
- enough GPU memory for the selected resolution and frame count.

Checkpoint and node names differ between installations. Export a working ComfyUI API workflow and update the workflow JSON or bindings when necessary. The application does not depend on SVD specifically; AnimateDiff, Wan, HunyuanVideo, LTX-Video, or another local workflow can replace it while preserving the same job API.

## Configuration

```env
VIDEO_PROVIDER=local-comfyui-video
VIDEO_BASE_URL=https://your-comfyui-endpoint
VIDEO_WORKFLOW_PATH=/workspace/workflows/comfyui/svd.json
VIDEO_CLIENT_ID=ai-cartoon-studio-video
VIDEO_TIMEOUT_SECONDS=1200
VIDEO_POLL_INTERVAL_SECONDS=3
```

`VIDEO_BASE_URL` may point to the same ComfyUI instance used for images or to a separate GPU worker. Do not expose an unauthenticated ComfyUI endpoint publicly; use a private tunnel, firewall rule, or reverse proxy with authentication.

## Production flow

```text
Approved direction
→ Approved and permanently stored keyframes
→ Animation plan
→ Upload keyframe to ComfyUI
→ Generate one video clip per shot
→ Copy the result into project storage
→ Human clip review
→ Voice and lip sync
```

The planner refuses to animate a keyframe that is incomplete, unapproved, missing from permanent storage, or no longer present on disk. It also refuses a shot longer than `max_clip_duration_seconds`; the shot must be split in the directing stage instead of being silently shortened.

## Durable outputs

Generated clips are downloaded immediately from the temporary provider and stored under:

```text
storage/<series-id>/animated-shots/<animation-job-id>/
```

Each stored file records its MIME type, byte size, SHA-256 checksum, and a stable `/artifacts/...` URL served by the FastAPI application. Closing the GPU session therefore does not invalidate approved clips.

## Review and retries

Every animated shot has independent status, attempts, provider job ID, error, result files, and review status. A failed clip can be retried without regenerating the story, screenplay, direction, references, keyframe, or other shots.

The next production stage must only consume animation jobs whose generation status is `succeeded` and review status is `approved`.
