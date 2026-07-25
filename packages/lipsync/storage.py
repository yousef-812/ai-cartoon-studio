import hashlib
import os
import re
from pathlib import Path

from packages.lipsync.models import RenderedLipSyncVideo
from packages.videos.models import GeneratedVideo


def persist_lip_sync_video(
    root_path: str,
    rendered: RenderedLipSyncVideo,
    *,
    series_id: str,
    job_id: str,
) -> GeneratedVideo:
    root = Path(root_path).resolve()
    directory = root / _safe(series_id) / "lip-sync-shots" / _safe(job_id)
    directory.mkdir(parents=True, exist_ok=True)
    suffix = _video_suffix(rendered.filename, rendered.mime_type)
    destination = directory / f"lip-sync{suffix}"
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_bytes(rendered.content)
    os.replace(temporary, destination)
    relative = destination.resolve().relative_to(root)
    return GeneratedVideo(
        url=f"/artifacts/{relative.as_posix()}",
        filename=destination.name,
        storage_path=str(destination),
        mime_type=rendered.mime_type,
        size_bytes=len(rendered.content),
        checksum_sha256=hashlib.sha256(rendered.content).hexdigest(),
        duration_seconds=rendered.duration_seconds,
        metadata=rendered.metadata,
    )


def _safe(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
    if not cleaned:
        raise ValueError("Lip-sync artifact path identifier is empty")
    return cleaned[:200]


def _video_suffix(filename: str, mime_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".mp4", ".webm", ".mov", ".mkv"}:
        return suffix
    return {
        "video/webm": ".webm",
        "video/quicktime": ".mov",
        "video/x-matroska": ".mkv",
    }.get(mime_type, ".mp4")
