# Self-hosted voice acting

AI Cartoon Studio treats speech synthesis as a replaceable worker. Character voice identities, screenplay lines, generation attempts, audio files, and review decisions remain in the project even if a temporary Lightning AI, Colab, or local speech server disconnects.

## Provider contract

The default adapter calls an OpenAI-compatible endpoint:

```text
POST /v1/audio/speech
```

The request includes the configured model, permanent `voice_id`, dialogue text, language, emotion, delivery, speed, pitch, and output format. A different local protocol can be implemented behind the same `AudioProvider` contract without changing voice jobs or the dashboard.

## Configuration

```env
VOICE_PROVIDER=local-openai-compatible-tts
VOICE_BASE_URL=https://your-private-tts-endpoint
VOICE_API_KEY=change-this-private-token
VOICE_MODEL=local-tts
VOICE_TIMEOUT_SECONDS=300
VOICE_MAX_RETRIES=2
```

The speech endpoint should remain private behind authentication, a firewall, or a private tunnel.

## Permanent character identity

Every speaking character must have a saved voice profile:

```text
provider
voice_id
language
description
speed
pitch
```

Voice planning fails when a screenplay references an unknown character or a character without `voice_id`. This prevents the same character from receiving a random voice in later episodes.

## Production flow

```text
Approved screenplay
→ Validate exact character names and voice profiles
→ One voice job per dialogue line
→ Self-hosted speech synthesis
→ Durable audio storage
→ Human voice review
→ Lip sync
```

Each voice job keeps the scene number, dialogue order, character, text, emotion, delivery direction, target duration, and pause after the line.

## Durable output

Generated audio is stored under:

```text
storage/<series-id>/voice-lines/<voice-job-id>/
```

The stored record includes a stable `/artifacts/...` URL, MIME type, byte size, SHA-256 checksum, expected duration, sample rate, and channel count when available.

## Review and retries

Every line can be retried or reviewed independently. Regenerating one emotional delivery does not regenerate the story, screenplay, direction, visual assets, animation, or other dialogue lines. Lip-sync jobs must consume only audio whose generation status is `succeeded` and review status is `approved`.
