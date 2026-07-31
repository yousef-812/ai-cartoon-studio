from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Header, HTTPException, Request, Response, status
from starlette.datastructures import UploadFile

MUSE_TALK_DIR = Path(os.getenv("MUSE_TALK_DIR", "/opt/MuseTalk")).resolve()
API_KEY = os.getenv("MUSE_TALK_API_KEY", "")
FFMPEG_PATH = os.getenv("MUSE_TALK_FFMPEG_PATH", str(Path(shutil.which("ffmpeg") or "/usr/bin/ffmpeg").parent))
INFERENCE_LOCK = threading.Lock()


def _authorize(authorization: str | None) -> None:
    if API_KEY and authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def _required_paths() -> list[Path]:
    return [
        MUSE_TALK_DIR / "scripts" / "inference.py",
        MUSE_TALK_DIR / "models" / "musetalkV15" / "unet.pth",
        MUSE_TALK_DIR / "models" / "musetalkV15" / "musetalk.json",
        MUSE_TALK_DIR / "models" / "whisper" / "config.json",
        MUSE_TALK_DIR / "models" / "sd-vae" / "config.json",
    ]


def _check_ready() -> tuple[bool, str]:
    missing = [str(path) for path in _required_paths() if not path.is_file()]
    if missing:
        return False, "Missing MuseTalk files: " + ", ".join(missing)
    if not shutil.which("ffmpeg"):
        return False, "FFmpeg is not installed"
    return True, "MuseTalk 1.5 model and FFmpeg are ready"


def _save_upload(upload: UploadFile, destination: Path) -> None:
    with destination.open("wb") as output:
        while chunk := upload.file.read(1024 * 1024):
            output.write(chunk)


def _prepare_video(source: Path, destination: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-vf",
            "fps=25,scale=1024:576:force_original_aspect_ratio=decrease,pad=1024:576:(ow-iw)/2:(oh-ih)/2",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(destination),
        ],
        check=True,
    )


def _prepare_audio(source: Path, destination: Path, start: float, duration: float) -> None:
    delay_ms = max(0, round(start * 1000))
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-af",
            f"adelay={delay_ms}|{delay_ms},apad,atrim=0:{duration:.3f}",
            "-ar",
            "16000",
            "-ac",
            "1",
            "-c:a",
            "pcm_s16le",
            str(destination),
        ],
        check=True,
    )


def _run_musetalk(video: Path, audio: Path, result_dir: Path, bbox_shift: int) -> Path:
    config_path = result_dir / "inference.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "task_0": {
                    "video_path": str(video),
                    "audio_path": str(audio),
                    "bbox_shift": bbox_shift,
                }
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "scripts.inference",
        "--inference_config",
        str(config_path),
        "--result_dir",
        str(result_dir),
        "--unet_model_path",
        "models/musetalkV15/unet.pth",
        "--unet_config",
        "models/musetalkV15/musetalk.json",
        "--version",
        "v15",
        "--ffmpeg_path",
        FFMPEG_PATH,
    ]
    with INFERENCE_LOCK:
        subprocess.run(command, cwd=MUSE_TALK_DIR, check=True)
    outputs = [path for path in result_dir.rglob("*.mp4") if path.is_file()]
    if not outputs:
        raise RuntimeError("MuseTalk did not create an MP4 output")
    return max(outputs, key=lambda path: path.stat().st_mtime)


def _finalize(source: Path, destination: Path, duration: float) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-movflags",
            "+faststart",
            str(destination),
        ],
        check=True,
    )


app = FastAPI(title="MuseTalk HTTP Provider", version="1.0.0")


@app.get("/health")
def health() -> dict[str, object]:
    available, detail = _check_ready()
    return {"available": available, "provider": "musetalk-v1.5", "detail": detail}


@app.post("/v1/lip-sync")
async def lip_sync(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Response:
    _authorize(authorization)
    available, detail = _check_ready()
    if not available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

    form = await request.form()
    manifest_value = form.get("manifest")
    video_upload = form.get("video")
    if not isinstance(manifest_value, str) or not isinstance(video_upload, UploadFile):
        raise HTTPException(status_code=400, detail="manifest and video are required")
    try:
        manifest: dict[str, Any] = json.loads(manifest_value)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="manifest is not valid JSON") from error

    segments = manifest.get("segments") or []
    if len(segments) != 1:
        raise HTTPException(
            status_code=409,
            detail="The first real episode profile requires exactly one speaking character per shot",
        )
    segment = segments[0]
    audio_upload = form.get(str(segment.get("audio_field", "audio_0")))
    if not isinstance(audio_upload, UploadFile):
        raise HTTPException(status_code=400, detail="The segment audio upload is missing")

    duration = float(manifest.get("duration_seconds", 0))
    start = float(segment.get("start_time_seconds", 0))
    if duration <= 0 or start < 0 or start >= duration:
        raise HTTPException(status_code=400, detail="Invalid lip-sync timeline")
    bbox_shift = int(manifest.get("metadata", {}).get("bbox_shift", 0))

    with tempfile.TemporaryDirectory(prefix="musetalk-http-") as temporary_directory:
        workdir = Path(temporary_directory)
        input_video = workdir / "input.mp4"
        input_audio = workdir / "speech.wav"
        prepared_video = workdir / "video-25fps.mp4"
        prepared_audio = workdir / "timeline.wav"
        result_dir = workdir / "results"
        final_path = workdir / "lip-sync.mp4"
        result_dir.mkdir()
        _save_upload(video_upload, input_video)
        _save_upload(audio_upload, input_audio)
        _prepare_video(input_video, prepared_video)
        _prepare_audio(input_audio, prepared_audio, start, duration)
        generated = _run_musetalk(prepared_video, prepared_audio, result_dir, bbox_shift)
        _finalize(generated, final_path, duration)
        content = final_path.read_bytes()
    return Response(content=content, media_type="video/mp4")
