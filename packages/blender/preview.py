import json
import subprocess
from pathlib import Path


def load_sequence(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("Blender sequence does not contain any shot items")
    return payload


def select_preview_items(
    sequence: dict[str, object],
    rendered_dir: Path,
    *,
    limit: int,
) -> list[dict[str, object]]:
    if limit < 0:
        raise ValueError("Preview shot limit cannot be negative")

    raw_items = sequence.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("Blender sequence items must be a list")
    selected = raw_items if limit == 0 else raw_items[:limit]
    if not selected:
        raise ValueError("No Blender shots were selected for the preview")

    resolved: list[dict[str, object]] = []
    missing: list[str] = []
    for raw in selected:
        if not isinstance(raw, dict):
            raise ValueError("Every Blender sequence item must be an object")
        output_name = str(raw.get("output", ""))
        if not output_name:
            raise ValueError("Blender sequence item is missing its output filename")
        video_path = rendered_dir / output_name
        if not video_path.is_file() or video_path.stat().st_size == 0:
            missing.append(output_name)
            continue
        resolved.append({**raw, "video_path": str(video_path.resolve())})

    if missing:
        raise FileNotFoundError(f"Rendered Blender shots are missing: {missing}")
    return resolved


def write_concat_manifest(items: list[dict[str, object]], path: Path) -> None:
    lines: list[str] = []
    for item in items:
        source = str(item["video_path"]).replace("\\", "/")
        if "'" in source:
            raise ValueError("Blender preview paths cannot contain single quotes")
        lines.append(f"file '{source}'")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_preview_command(
    concat_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    fps: int,
    ffmpeg_binary: str = "ffmpeg",
) -> list[str]:
    video_filter = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={fps}"
    )
    return [
        ffmpeg_binary,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-map",
        "0:v:0",
        "-vf",
        video_filter,
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def probe_video(path: Path, *, ffprobe_binary: str = "ffprobe") -> dict[str, object]:
    result = subprocess.run(
        [
            ffprobe_binary,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate:format=duration",
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
        raise RuntimeError(f"No video stream found in Blender output: {path}")
    stream = streams[0]
    rate = str(stream.get("r_frame_rate", "0/1"))
    numerator, _, denominator = rate.partition("/")
    fps = float(numerator) / max(float(denominator or 1), 1.0)
    duration = float(payload.get("format", {}).get("duration", 0.0))
    return {
        "width": int(stream.get("width", 0)),
        "height": int(stream.get("height", 0)),
        "fps": fps,
        "duration_seconds": duration,
        "size_bytes": path.stat().st_size,
    }


def build_preview(
    sequence_path: Path,
    rendered_dir: Path,
    output_path: Path,
    report_path: Path,
    *,
    limit: int = 3,
    ffmpeg_binary: str = "ffmpeg",
    ffprobe_binary: str = "ffprobe",
) -> dict[str, object]:
    sequence = load_sequence(sequence_path)
    items = select_preview_items(sequence, rendered_dir, limit=limit)
    concat_path = output_path.with_suffix(".concat.txt")
    write_concat_manifest(items, concat_path)

    probes: list[dict[str, object]] = []
    for item in items:
        video_path = Path(str(item["video_path"]))
        probe = probe_video(video_path, ffprobe_binary=ffprobe_binary)
        expected = float(item.get("duration_seconds", 0.0))
        probes.append(
            {
                "scene_number": item.get("scene_number"),
                "shot_number": item.get("shot_number"),
                "shot_key": item.get("shot_key"),
                "file": video_path.name,
                "expected_duration_seconds": expected,
                **probe,
                "duration_ok": abs(float(probe["duration_seconds"]) - expected) <= 0.25,
            }
        )

    first = probes[0]
    width = int(first["width"])
    height = int(first["height"])
    fps = max(1, round(float(first["fps"])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        build_preview_command(
            concat_path,
            output_path,
            width=width,
            height=height,
            fps=fps,
            ffmpeg_binary=ffmpeg_binary,
        ),
        check=True,
    )
    output_probe = probe_video(output_path, ffprobe_binary=ffprobe_binary)

    report = {
        "status": "preview_succeeded",
        "episode_title": sequence.get("episode_title", ""),
        "selected_shots": len(items),
        "planned_shots": sequence.get("shot_count", len(items)),
        "expected_duration_seconds": sum(
            float(item.get("duration_seconds", 0.0)) for item in items
        ),
        "preview": str(output_path.resolve()),
        "preview_probe": output_probe,
        "shots": probes,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
