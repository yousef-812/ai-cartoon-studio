from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, Field

VOICE_NAME = os.getenv("PIPER_VOICE_NAME", "ar_JO-kareem-medium")
DATA_DIR = Path(os.getenv("PIPER_DATA_DIR", "/models")).resolve()
API_KEY = os.getenv("PIPER_API_KEY", "")
SAMPLE_RATE = int(os.getenv("PIPER_SAMPLE_RATE", "22050"))
_MODEL_LOCK = threading.Lock()


class SpeechRequest(BaseModel):
    model: str = "piper-arabic"
    input: str = Field(min_length=1, max_length=10000)
    voice: str = VOICE_NAME
    response_format: str = Field(default="wav", pattern=r"^(wav|mp3|flac|opus)$")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    language: str = "ar"
    emotion: str = "neutral"
    delivery: str = ""
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


def _model_path() -> Path:
    return DATA_DIR / f"{VOICE_NAME}.onnx"


def _ensure_authorized(authorization: str | None) -> None:
    if not API_KEY:
        return
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _ensure_voice() -> Path:
    model = _model_path()
    if model.is_file() and model.with_suffix(".onnx.json").is_file():
        return model
    with _MODEL_LOCK:
        if model.is_file() and model.with_suffix(".onnx.json").is_file():
            return model
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper.download_voices",
                "--data-dir",
                str(DATA_DIR),
                VOICE_NAME,
            ],
            check=True,
        )
    if not model.is_file():
        raise RuntimeError(f"Piper voice download did not create {model}")
    return model


def _atempo_filters(value: float) -> list[str]:
    factors: list[float] = []
    remaining = value
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return [f"atempo={factor:.6f}" for factor in factors]


def _convert_audio(source: Path, destination: Path, request: SpeechRequest) -> None:
    tempo = request.speed / request.pitch
    filters = [
        f"asetrate={SAMPLE_RATE}*{request.pitch:.6f}",
        f"aresample={SAMPLE_RATE}",
        *_atempo_filters(tempo),
        "loudnorm=I=-18:TP=-2:LRA=7",
    ]
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-af",
        ",".join(filters),
    ]
    codec_args = {
        "wav": ["-c:a", "pcm_s16le"],
        "mp3": ["-c:a", "libmp3lame", "-b:a", "160k"],
        "flac": ["-c:a", "flac"],
        "opus": ["-c:a", "libopus", "-b:a", "96k"],
    }[request.response_format]
    subprocess.run([*command, *codec_args, str(destination)], check=True)


app = FastAPI(title="Piper OpenAI-compatible TTS", version="1.0.0")


@app.get("/health")
def health() -> dict[str, object]:
    try:
        model = _ensure_voice()
    except (OSError, subprocess.SubprocessError, RuntimeError) as error:
        return {"available": False, "voice": VOICE_NAME, "detail": str(error)}
    return {
        "available": bool(shutil.which("ffmpeg") and model.is_file()),
        "voice": VOICE_NAME,
        "model_path": str(model),
        "detail": "Piper Arabic voice and FFmpeg are ready",
    }


@app.get("/v1/models")
def models(authorization: str | None = Header(default=None)) -> dict[str, object]:
    _ensure_authorized(authorization)
    _ensure_voice()
    return {
        "object": "list",
        "data": [
            {
                "id": "piper-arabic",
                "object": "model",
                "owned_by": "local",
                "voice": VOICE_NAME,
            }
        ],
    }


@app.post("/v1/audio/speech")
def speech(
    request: SpeechRequest,
    authorization: str | None = Header(default=None),
) -> Response:
    _ensure_authorized(authorization)
    model = _ensure_voice()
    with tempfile.TemporaryDirectory(prefix="piper-tts-") as temporary_directory:
        workdir = Path(temporary_directory)
        raw_path = workdir / "raw.wav"
        output_path = workdir / f"speech.{request.response_format}"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "piper",
                "-m",
                str(model),
                "-f",
                str(raw_path),
                "--",
                request.input,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        _convert_audio(raw_path, output_path, request)
        content = output_path.read_bytes()
    mime_type = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "flac": "audio/flac",
        "opus": "audio/ogg",
    }[request.response_format]
    return Response(content=content, media_type=mime_type)
