import json
import re
import subprocess
from pathlib import Path

from packages.finalization.models import QCCheck, QCSeverity


_SILENCE_RE = re.compile(r"silence_duration:\s*([0-9.]+)")
_MAX_VOLUME_RE = re.compile(r"max_volume:\s*(-?[0-9.]+) dB")


def parse_silence_durations(stderr: str) -> list[float]:
    return [float(value) for value in _SILENCE_RE.findall(stderr)]


def parse_max_volume(stderr: str) -> float | None:
    match = _MAX_VOLUME_RE.search(stderr)
    return float(match.group(1)) if match else None


def inspect_media(
    path: str,
    *,
    expected_duration: float,
    silence_threshold_db: float,
    max_silence_seconds: float,
    max_peak_db: float,
    ffmpeg_binary: str = "ffmpeg",
    ffprobe_binary: str = "ffprobe",
) -> list[QCCheck]:
    source = Path(path)
    if not source.is_file():
        return [QCCheck(code="file_exists", severity=QCSeverity.ERROR, passed=False, message=f"Media file is missing: {path}")]

    probe = subprocess.run(
        [ffprobe_binary, "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(probe.stdout)
    streams = payload.get("streams", [])
    has_video = any(stream.get("codec_type") == "video" for stream in streams)
    has_audio = any(stream.get("codec_type") == "audio" for stream in streams)
    duration = float(payload.get("format", {}).get("duration") or expected_duration)
    checks = [
        QCCheck(code="video_stream", severity=QCSeverity.ERROR, passed=has_video, message="Video stream is present" if has_video else "Video stream is missing"),
        QCCheck(code="audio_stream", severity=QCSeverity.ERROR, passed=has_audio, message="Audio stream is present" if has_audio else "Audio stream is missing"),
        QCCheck(
            code="duration_match",
            severity=QCSeverity.ERROR,
            passed=abs(duration - expected_duration) <= 0.35,
            message=f"Media duration is {duration:.3f}s; expected {expected_duration:.3f}s",
            metadata={"actual": duration, "expected": expected_duration},
        ),
    ]
    audio = subprocess.run(
        [
            ffmpeg_binary,
            "-hide_banner",
            "-i",
            path,
            "-af",
            f"silencedetect=noise={silence_threshold_db}dB:d=0.2,volumedetect",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    silences = parse_silence_durations(audio.stderr)
    longest = max(silences, default=0.0)
    peak = parse_max_volume(audio.stderr)
    checks.append(
        QCCheck(
            code="excessive_silence",
            severity=QCSeverity.WARNING,
            passed=longest <= max_silence_seconds,
            message=f"Longest detected silence is {longest:.3f}s",
            metadata={"longest_silence_seconds": longest},
        )
    )
    checks.append(
        QCCheck(
            code="audio_peak",
            severity=QCSeverity.ERROR,
            passed=peak is not None and peak <= max_peak_db,
            message="Audio peak could not be measured" if peak is None else f"Maximum audio peak is {peak:.2f} dB",
            metadata={"max_volume_db": peak},
        )
    )
    return checks
