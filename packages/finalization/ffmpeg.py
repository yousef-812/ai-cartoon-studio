import subprocess
from pathlib import Path

from packages.finalization.models import FinalizationJobSpec, ShortCandidateSpec


def write_concat_manifest(spec: FinalizationJobSpec, path: Path) -> None:
    lines = []
    for shot in spec.shots:
        source = Path(shot.input_video_path).resolve().as_posix()
        if "'" in source:
            raise ValueError("Finalization media paths cannot contain single quotes")
        lines.append(f"file '{source}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_concat_command(
    manifest_path: str,
    output_path: str,
    spec: FinalizationJobSpec,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    request = spec.request
    video_filter = (
        f"scale={request.output_width}:{request.output_height}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={request.output_width}:{request.output_height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={request.output_fps}"
    )
    audio_filter = (
        f"loudnorm=I={request.target_loudness_lufs}:"
        f"TP={request.max_peak_db}:LRA=11"
    )
    return [
        ffmpeg_binary,
        "-y",
        "-hide_banner",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        manifest_path,
        "-vf",
        video_filter,
        "-af",
        audio_filter,
        "-c:v",
        request.video_codec,
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        request.audio_codec,
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        output_path,
    ]


def render_episode(
    spec: FinalizationJobSpec,
    manifest_path: str,
    output_path: str,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    subprocess.run(
        build_concat_command(
            manifest_path,
            output_path,
            spec,
            ffmpeg_binary=ffmpeg_binary,
        ),
        check=True,
        capture_output=True,
        text=True,
    )


def burn_subtitles(
    input_path: str,
    subtitle_path: str,
    output_path: str,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    normalized = subtitle_path.replace("\\", "/").replace(":", "\\:")
    subprocess.run(
        [
            ffmpeg_binary,
            "-y",
            "-hide_banner",
            "-i",
            input_path,
            "-vf",
            f"subtitles={normalized}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "copy",
            "-movflags",
            "+faststart",
            output_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def extract_thumbnail(
    input_path: str,
    output_path: str,
    timestamp_seconds: float,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> None:
    subprocess.run(
        [
            ffmpeg_binary,
            "-y",
            "-hide_banner",
            "-ss",
            f"{timestamp_seconds:.3f}",
            "-i",
            input_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            output_path,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def build_short_command(
    input_path: str,
    output_path: str,
    candidate: ShortCandidateSpec,
    *,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_binary,
        "-y",
        "-hide_banner",
        "-ss",
        f"{candidate.start_time_seconds:.3f}",
        "-t",
        f"{candidate.duration_seconds:.3f}",
        "-i",
        input_path,
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        output_path,
    ]
