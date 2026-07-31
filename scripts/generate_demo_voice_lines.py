#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_TARGET_SAMPLE_RATE = 48000
_TARGET_CHANNELS = 1


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _endpoint(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    if path.startswith("v1/") and base.endswith("/v1"):
        return f"{base}/{path[3:]}"
    return f"{base}/{path.lstrip('/')}"


def _request_json(url: str, *, api_key: str = "") -> dict[str, object]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _synthesize(
    base_url: str,
    payload: dict[str, object],
    *,
    api_key: str,
    timeout_seconds: int,
) -> bytes:
    headers = {
        "Accept": "audio/wav",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(
        _endpoint(base_url, "v1/audio/speech"),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        content = response.read()
    if not content:
        raise RuntimeError("Piper returned an empty audio response")
    return content


def _probe_audio(path: Path, ffprobe_binary: str) -> dict[str, object]:
    result = subprocess.run(
        [
            ffprobe_binary,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    streams = payload.get("streams", [])
    if not streams:
        raise RuntimeError(f"Generated speech has no audio stream: {path}")
    stream = streams[0]
    return {
        "duration_seconds": float(payload.get("format", {}).get("duration", 0.0)),
        "sample_rate": int(stream.get("sample_rate", 0)),
        "channels": int(stream.get("channels", 0)),
        "size_bytes": path.stat().st_size,
    }


def _normalize_wav(path: Path, ffmpeg_binary: str) -> None:
    temporary = path.with_name(f"{path.stem}.normalized.wav")
    temporary.unlink(missing_ok=True)
    try:
        subprocess.run(
            [
                ffmpeg_binary,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(path),
                "-ar",
                str(_TARGET_SAMPLE_RATE),
                "-ac",
                str(_TARGET_CHANNELS),
                "-c:a",
                "pcm_s16le",
                str(temporary),
            ],
            check=True,
        )
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg did not create normalized speech: {temporary}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def generate(
    screenplay_path: Path,
    characters_path: Path,
    output_dir: Path,
    *,
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: int,
    ffmpeg_binary: str,
    ffprobe_binary: str,
    force: bool,
) -> dict[str, object]:
    screenplay = _read_json(screenplay_path)
    characters = _read_json(characters_path)
    if not isinstance(characters, list):
        raise ValueError("Characters file must contain a list")
    character_map = {
        str(character.get("name", "")): character
        for character in characters
        if isinstance(character, dict)
    }

    health = _request_json(_endpoint(base_url, "health"), api_key=api_key)
    if not bool(health.get("available")):
        raise RuntimeError(f"Piper is not ready: {health.get('detail', health)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    lines: list[dict[str, object]] = []
    scenes = screenplay.get("scenes", [])
    if not isinstance(scenes, list):
        raise ValueError("Screenplay does not contain a scenes list")

    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Every screenplay scene must be an object")
        scene_number = int(scene["number"])
        dialogue = scene.get("dialogue", [])
        if not isinstance(dialogue, list):
            raise ValueError(f"Scene {scene_number} dialogue must be a list")
        for line in dialogue:
            if not isinstance(line, dict):
                raise ValueError(f"Scene {scene_number} contains an invalid dialogue line")
            order = int(line["order"])
            speaker = str(line["speaker"])
            character = character_map.get(speaker)
            if character is None:
                raise ValueError(f"Dialogue speaker is not registered: {speaker}")
            profile = character.get("voice_profile", {})
            if not isinstance(profile, dict) or not profile.get("voice_id"):
                raise ValueError(f"Character {speaker} does not have a permanent voice_id")

            path = output_dir / f"scene_{scene_number:02d}_line_{order:02d}.wav"
            payload = {
                "model": model,
                "input": str(line["text"]),
                "voice": str(profile["voice_id"]),
                "response_format": "wav",
                "speed": float(profile.get("speed", 1.0)),
                "language": str(profile.get("language") or screenplay.get("language", "ar")),
                "emotion": str(line.get("emotion", "neutral")),
                "delivery": str(line.get("delivery", "natural")),
                "pitch": float(profile.get("pitch", 1.0)),
            }
            generated = force or not path.is_file() or path.stat().st_size == 0
            if generated:
                path.write_bytes(
                    _synthesize(
                        base_url,
                        payload,
                        api_key=api_key,
                        timeout_seconds=timeout_seconds,
                    )
                )

            probe = _probe_audio(path, ffprobe_binary)
            normalized = (
                int(probe["sample_rate"]) != _TARGET_SAMPLE_RATE
                or int(probe["channels"]) != _TARGET_CHANNELS
            )
            if normalized:
                _normalize_wav(path, ffmpeg_binary)
                probe = _probe_audio(path, ffprobe_binary)
            if int(probe["sample_rate"]) != _TARGET_SAMPLE_RATE:
                raise RuntimeError(f"Speech sample rate was not normalized: {path}")
            if int(probe["channels"]) != _TARGET_CHANNELS:
                raise RuntimeError(f"Speech channel count was not normalized: {path}")

            lines.append(
                {
                    "scene_number": scene_number,
                    "dialogue_order": order,
                    "speaker": speaker,
                    "text": str(line["text"]),
                    "voice_id": str(profile["voice_id"]),
                    "speed": payload["speed"],
                    "pitch": payload["pitch"],
                    "estimated_duration_seconds": float(
                        line.get("estimated_duration_seconds", 0.0)
                    ),
                    "generated": generated,
                    "normalized": normalized,
                    "file": str(path.resolve()),
                    **probe,
                }
            )
            print(
                f"VOICE_LINE_READY=scene:{scene_number}:line:{order}:"
                f"{speaker}:{probe['duration_seconds']:.3f}s:"
                f"{probe['sample_rate']}Hz:{probe['channels']}ch"
            )

    if not lines:
        raise ValueError("Screenplay does not contain dialogue to synthesize")
    report = {
        "status": "voice_generation_succeeded",
        "provider": "piper-openai-compatible",
        "base_url": base_url,
        "model": model,
        "target_sample_rate": _TARGET_SAMPLE_RATE,
        "target_channels": _TARGET_CHANNELS,
        "line_count": len(lines),
        "total_audio_seconds": sum(float(item["duration_seconds"]) for item in lines),
        "lines": lines,
    }
    report_path = output_dir / "voice_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"VOICE_GENERATION_SUCCEEDED={output_dir.resolve()}")
    print(f"VOICE_GENERATION_REPORT={report_path.resolve()}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate one Piper WAV file for every screenplay dialogue line."
    )
    parser.add_argument(
        "--screenplay",
        default="demo/first-real-episode/approved/screenplay.json",
    )
    parser.add_argument(
        "--characters",
        default="demo/first-real-episode/characters.json",
    )
    parser.add_argument("--output-dir", default="output/voices")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--model", default="piper-arabic")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--ffmpeg-binary", default="ffmpeg")
    parser.add_argument("--ffprobe-binary", default="ffprobe")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    try:
        generate(
            Path(args.screenplay),
            Path(args.characters),
            Path(args.output_dir),
            base_url=args.base_url,
            api_key=args.api_key,
            model=args.model,
            timeout_seconds=args.timeout_seconds,
            ffmpeg_binary=args.ffmpeg_binary,
            ffprobe_binary=args.ffprobe_binary,
            force=args.force,
        )
    except (
        OSError,
        ValueError,
        RuntimeError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
        urllib.error.URLError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
