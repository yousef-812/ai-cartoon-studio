# First real episode runbook

This runbook produces one complete original Arabic cartoon episode through the real production pipeline. The baseline is deliberately small enough for a free 16 GB-class GPU while still exercising every stage.

## Test target

- Series: `ورشة النور`
- Episode: emergency-lamp repair during a rainstorm
- Language: Modern Standard Arabic
- Characters: `عمر` and `نادر`
- Locations: one approved workshop
- Duration: approximately 40 seconds
- Direction target: exactly 10 shots
- Shot duration: 3.5–4.0 seconds
- Dialogue: at most one short sentence and one speaker per shot
- Visual generation: SDXL at 1024×576
- Animation: SVD 1.1 at 6 fps and 21–24 frames per shot
- Final delivery: 1920×1080, 24 fps, stereo 48 kHz, target -16 LUFS

The source bible, character identities, location, story request, and model manifest are in `demo/first-real-episode/`.

## What is already supplied

- Original series, characters, location, premise, continuity rules, visual prompts, and voice identities.
- A seed script that creates the demo records and queues the Story Job.
- Qwen llama.cpp launchers.
- SDXL and SVD ComfyUI workflows.
- ComfyUI setup and model-download script.
- Piper Arabic TTS with an OpenAI-compatible API.
- MuseTalk 1.5 HTTP wrapper.
- Original procedural ambience, effects, and music provider.
- FFmpeg mixing, subtitles, quality control, final master, thumbnail, and Shorts generation.
- A provider preflight checker for every stage.

## The only external requirements

1. Docker Desktop on the main machine.
2. One NVIDIA GPU runtime for the heavy stages. A free Lightning, Colab, Kaggle, or local CUDA machine can be used.
3. A Hugging Face token after accepting the SDXL and SVD repository terms.
4. Stable public or private URLs for ports `8080`, `8188`, and `8090` when the GPU is remote.

Do not add copyrighted character images, celebrity photographs, downloaded music, or third-party sound effects to this test.

## 1. Prepare the main project

Use the feature branch containing the complete pipeline:

```bash
git checkout agent/series-bible-foundation
cp .env.demo.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.demo.example .env
```

Change the demo tokens in `.env`. When the GPU is remote, replace these values with the exposed runtime URLs:

```env
LLM_BASE_URL=https://your-gpu-llm-url
IMAGE_BASE_URL=https://your-gpu-comfy-url
VIDEO_BASE_URL=https://your-gpu-comfy-url
LIP_SYNC_BASE_URL=https://your-gpu-musetalk-url
```

Start the CPU services:

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml up --build -d
```

This starts PostgreSQL, Redis, FastAPI, Celery, Next.js, Piper TTS, the procedural sound service, FFmpeg, and durable storage. Piper downloads the Arabic voice on its first start.

Check the permanent CPU stack:

```bash
python scripts/check_demo_stack.py --stage core
```

Every line must be `[ OK ]` before continuing.

## 2. Start Qwen and generate pre-production

On the GPU runtime, clone this repository and build llama.cpp:

```bash
bash scripts/setup_demo_llama_cpp.sh
```

Start Qwen3 8B Q4_K_M:

```bash
export HF_TOKEN=your_hugging_face_token
LLAMA_SERVER_BIN="$PWD/.runtime/llama.cpp/build/bin/llama-server" \
  bash scripts/start_demo_llm.sh
```

Expose port `8080`, update `LLM_BASE_URL` in the main `.env`, and recreate only the API and worker when the URL changed:

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --force-recreate api worker
python scripts/check_demo_stack.py --stage llm
```

Seed the original demo source and queue the Story Job:

```bash
python scripts/seed_first_real_episode.py
```

Then use the dashboards in order:

1. `/production` — review and approve the story.
2. Generate the screenplay, verify Arabic dialogue and timing, then approve it.
3. Generate direction, verify exactly 10 shots at 3.5–4.0 seconds each, then approve it.
4. Reject and regenerate any result that adds a third character, a second location, overlapping speakers, or long dialogue.

After direction is approved and permanently stored, Qwen can be stopped to release GPU memory.

## 3. Start ComfyUI and generate the visuals

On the GPU runtime:

```bash
export HF_TOKEN=your_hugging_face_token
bash scripts/setup_demo_comfyui.sh
```

The script installs ComfyUI and VideoHelperSuite, downloads the exact SDXL and SVD checkpoint filenames expected by the workflows, and starts port `8188`.

Expose port `8188`, update `IMAGE_BASE_URL` and `VIDEO_BASE_URL`, recreate the API and worker when needed, then check the stage:

```bash
python scripts/check_demo_stack.py --stage visual
```

Production order:

1. Open `/visuals` and create the asset manifest.
2. Generate Omar's character reference. Reject it unless the round glasses, teal jacket, face, and hair are clear.
3. Generate Nader's character reference. Reject it unless the orange hoodie, navy apron, face, and hair are clear.
4. Generate and approve the master workshop background. The storm window must stay camera-left and the main bench must remain centered.
5. Generate all 10 keyframes. Compare every frame with the approved references before approval.
6. Open `/animations` and generate clips with:
   - width `1024`
   - height `576`
   - fps `6`
   - duration copied from direction and never above `4.0` seconds
   - motion strength around `0.04–0.08`
   - 22 steps as the baseline
7. Approve only clips with stable faces, clothing, workshop layout, and readable action.

All approved images and videos are copied into project storage. ComfyUI may be stopped after every required clip is approved.

## 4. Generate and approve Arabic voices

Piper is already running on the CPU service.

1. Open `/voices`.
2. Create the voice plan from the approved screenplay.
3. Listen to every line.
4. Verify that Omar is slower and lower, while Nader is faster and slightly higher.
5. Reject mispronounced, clipped, or overlong lines.
6. Approve every final line.

Keep each line shorter than the directed speaking window. Do not compress a long sentence to force it into a short shot.

## 5. Start MuseTalk and run lip sync

Stop Qwen and ComfyUI first when the same GPU runtime is used. Then run:

```bash
bash scripts/setup_demo_musetalk.sh
```

The script follows the official MuseTalk dependency and weight layout and starts the project HTTP wrapper on port `8090`.

Expose port `8090`, update `LIP_SYNC_BASE_URL`, recreate the API and worker, and verify:

```bash
python scripts/check_demo_stack.py --stage lip-sync
```

Open `/lip-sync`, create the plan, and verify:

- exactly one speaking segment per speaking shot;
- the correct character face is visible in front or three-quarter view;
- mouth motion starts and ends with the approved audio window;
- non-speaking shots remain animation sources and are not passed through lip sync.

Approve each valid result separately.

## 6. Build the soundtrack

Open `/sound-design` and create the sound plan with:

- ambience enabled;
- effects enabled;
- instrumental music enabled;
- ambience gain near `-20 dB`;
- effects gain near `-12 dB`;
- music gain near `-22 dB`;
- dialogue ducking near `-10 dB`;
- target loudness `-16 LUFS`.

The baseline provider creates original rain/workshop ambience, simple repair and spark effects, and a generated chord score from code. No downloaded audio asset is used.

Listen to each layer, approve every shot mix, and reject any mix that hides dialogue or contains excessive silence.

## 7. Assemble and validate the episode

Open `/finalization` and use:

- output width `1920`;
- output height `1080`;
- output fps `24`;
- video codec `libx264`;
- audio codec `aac`;
- subtitles enabled;
- subtitle language `ar`;
- target loudness `-16 LUFS`;
- peak ceiling `-1 dB`;
- thumbnail enabled;
- one or two Shorts candidates for this short technical episode.

The final job must create:

```text
episode-master.mp4
episode.srt
episode.vtt
qc-report.json
thumbnail.jpg
short-1.mp4
```

Approve the episode only when the QC report passes video stream, audio stream, duration, peak, loudness, and subtitle-bound checks.

## Acceptance checklist

The baseline real test passes only when all statements are true:

- 10 directed shots exist and all have approved final sound mixes.
- Omar's glasses and teal jacket remain recognizable.
- Nader's orange hoodie and navy apron remain recognizable.
- The workshop window, bench, and emergency lamp remain spatially consistent.
- No shot contains two speaking segments.
- Every spoken line has approved audio and lip sync.
- The final master is approximately 40 seconds and contains both video and audio.
- SRT and VTT timings remain inside the episode duration.
- The final QC JSON has no blocking errors.
- All final files use permanent `/artifacts/...` URLs.

## Recovery rules

- A failed Story, Script, or Direction Job is retried without touching the series bible.
- A bad image regenerates only that visual asset.
- A bad animation regenerates only that shot.
- A bad voice regenerates only that dialogue line.
- A bad lip sync regenerates only that speaking shot.
- A bad sound mix regenerates only that shot mix.
- Finalization runs only after every upstream item is successful and approved.

The first run is a technical baseline, not the final artistic quality target. After this episode passes end to end, increase identity consistency with an SDXL IP-Adapter workflow and then scale episode duration toward 2–4 minutes.
