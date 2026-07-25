# Lip sync and dialogue placement

AI Cartoon Studio treats dialogue placement as permanent production data rather than an implicit side effect of a model call.

## Review gate

A lip-sync plan can be created only when all of the following are true:

- the direction job succeeded and is approved;
- the source animated shot succeeded and is approved;
- every dialogue line assigned to the shot has a successful, approved voice job;
- the source MP4 and every audio file exist in durable project storage;
- the planned dialogue timeline fits inside the animated shot duration.

The planner never silently truncates dialogue or compresses it to hide a timing conflict. A timing conflict must be fixed by splitting the shot, changing direction, shortening the line, or regenerating the voice timing.

## Multi-speaker shots

One lip-sync job is created per directed shot. The job contains one or more ordered dialogue segments. Every segment records:

- exact voice job and character identity;
- dialogue order and text;
- audio storage path;
- start and end time inside the shot;
- pause after the line;
- face-tracking hint for the speaking character.

This allows two or more characters to speak in the same shot without losing the final shot-level artifact. The provider receives the source video once, all required audio files, and one JSON manifest.

## Self-hosted provider contract

Configure:

```env
LIP_SYNC_PROVIDER=local-lip-sync-http
LIP_SYNC_BASE_URL=https://your-private-gpu-endpoint
LIP_SYNC_ENDPOINT_PATH=/v1/lip-sync
LIP_SYNC_API_KEY=private-token
LIP_SYNC_TIMEOUT_SECONDS=1200
```

The API sends a multipart `POST` request to `/v1/lip-sync` containing:

- `video`: the approved source animated shot;
- `audio_0`, `audio_1`, and so on: approved dialogue audio files;
- `manifest`: JSON describing timing, speaker identity, face hints, quality, model, constraints, and metadata.

The endpoint must return the completed video body with `video/mp4`, `video/webm`, or `video/quicktime` content type. This contract can wrap MuseTalk, Wav2Lip, LatentSync, a ComfyUI workflow, or another self-hosted implementation without changing production records.

## Durable result

Completed videos are stored under:

```text
storage/<series-id>/lip-sync-shots/<job-id>/lip-sync.mp4
```

The database stores a stable `/artifacts/...` URL, MIME type, byte size, SHA-256 checksum, duration, source IDs, attempts, errors, and human review decision.

## Dashboard

Open `/lip-sync` to:

- check provider health;
- select an approved direction;
- configure lead-in, tail padding, minimum dialogue gap, model, quality, and face confidence;
- inspect every dialogue segment on the shot timeline;
- retry failed shots independently;
- approve mouth movement and dialogue placement or request changes.

The next stage consumes only approved lip-sync shots and adds ambience, sound effects, music, and final dialogue mixing.
