from __future__ import annotations

import hashlib
import io
import math
import os
import wave

import numpy as np
from fastapi import FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

SAMPLE_RATE = int(os.getenv("SOUND_SAMPLE_RATE", "48000"))
API_KEY = os.getenv("SOUND_API_KEY", "")


class SoundRequest(BaseModel):
    kind: str = Field(pattern=r"^(ambience|effect|music)$")
    prompt: str = Field(min_length=3, max_length=5000)
    duration_seconds: float = Field(ge=0.1, le=600)
    model: str = "procedural-demo-v1"
    seed: int | None = None
    loop: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


def _authorize(authorization: str | None) -> None:
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _seed(request: SoundRequest) -> int:
    if request.seed is not None:
        return request.seed
    digest = hashlib.sha256(f"{request.kind}:{request.prompt}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _fade(signal: np.ndarray, seconds: float = 0.08) -> np.ndarray:
    samples = min(len(signal) // 2, max(1, int(seconds * SAMPLE_RATE)))
    envelope = np.ones(len(signal), dtype=np.float32)
    envelope[:samples] = np.linspace(0, 1, samples, dtype=np.float32)
    envelope[-samples:] = np.linspace(1, 0, samples, dtype=np.float32)
    return signal * envelope


def _ambience(request: SoundRequest, rng: np.random.Generator) -> np.ndarray:
    count = max(1, int(request.duration_seconds * SAMPLE_RATE))
    time = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    noise = rng.normal(0, 1, count).astype(np.float32)
    smoothed = np.convolve(noise, np.ones(80, dtype=np.float32) / 80, mode="same")
    rain = noise * 0.025 + smoothed * 0.12
    rumble = np.sin(2 * math.pi * 42 * time) * 0.025
    workshop_hum = np.sin(2 * math.pi * 60 * time) * 0.012
    prompt = request.prompt.lower()
    if "rain" not in prompt and "storm" not in prompt and "مطر" not in prompt:
        rain *= 0.45
    return _fade(rain + rumble + workshop_hum, 0.25)


def _effect(request: SoundRequest, rng: np.random.Generator) -> np.ndarray:
    count = max(1, int(request.duration_seconds * SAMPLE_RATE))
    time = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    signal = np.zeros(count, dtype=np.float32)
    prompt = request.prompt.lower()
    if any(token in prompt for token in ("spark", "شرار", "electric")):
        burst = rng.normal(0, 1, count).astype(np.float32)
        envelope = np.exp(-time * 24)
        signal = burst * envelope * 0.35 + np.sin(2 * math.pi * 1600 * time) * envelope * 0.12
    elif any(token in prompt for token in ("tool", "metal", "screw", "أداة", "مفك")):
        envelope = np.exp(-time * 18)
        signal = (
            np.sin(2 * math.pi * 880 * time)
            + 0.6 * np.sin(2 * math.pi * 1320 * time)
        ) * envelope * 0.22
    elif any(token in prompt for token in ("lamp", "switch", "مصباح", "زر")):
        envelope = np.exp(-time * 35)
        signal = np.sin(2 * math.pi * 420 * time) * envelope * 0.3
    else:
        envelope = np.exp(-time * 20)
        signal = rng.normal(0, 1, count).astype(np.float32) * envelope * 0.16
    return _fade(signal, 0.01)


def _music(request: SoundRequest, rng: np.random.Generator) -> np.ndarray:
    del rng
    count = max(1, int(request.duration_seconds * SAMPLE_RATE))
    time = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    progression = [
        (220.00, 261.63, 329.63),
        (174.61, 220.00, 261.63),
        (196.00, 246.94, 293.66),
        (164.81, 207.65, 261.63),
    ]
    chord_seconds = 2.0
    signal = np.zeros(count, dtype=np.float32)
    for index in range(count):
        chord = progression[int((index / SAMPLE_RATE) / chord_seconds) % len(progression)]
        t = time[index]
        signal[index] = sum(
            math.sin(2 * math.pi * frequency * t) + 0.22 * math.sin(4 * math.pi * frequency * t)
            for frequency in chord
        ) / (len(chord) * 5.0)
    pulse = 0.8 + 0.2 * np.sin(2 * math.pi * 0.5 * time)
    return _fade(signal * pulse, 0.5)


def _wav_bytes(signal: np.ndarray) -> bytes:
    peak = float(np.max(np.abs(signal))) if signal.size else 1.0
    if peak > 0.95:
        signal = signal * (0.95 / peak)
    pcm = np.clip(signal, -1, 1)
    pcm16 = (pcm * 32767).astype("<i2")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm16.tobytes())
    return buffer.getvalue()


app = FastAPI(title="Procedural Demo Sound Provider", version="1.0.0")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "available": True,
        "provider": "procedural-demo-v1",
        "sample_rate": SAMPLE_RATE,
        "detail": "Original procedural ambience, effects, and music are ready",
    }


@app.post("/v1/audio/generate")
def generate(
    request: SoundRequest,
    authorization: str | None = Header(default=None),
) -> Response:
    _authorize(authorization)
    rng = np.random.default_rng(_seed(request))
    if request.kind == "ambience":
        signal = _ambience(request, rng)
    elif request.kind == "effect":
        signal = _effect(request, rng)
    else:
        signal = _music(request, rng)
    return Response(content=_wav_bytes(signal), media_type="audio/wav")
