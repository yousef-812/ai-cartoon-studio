import hashlib
import os
import re
from pathlib import Path

from packages.finalization.models import FinalArtifact


_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".srt": "application/x-subrip",
    ".vtt": "text/vtt",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


class FinalArtifactStore:
    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path).resolve()

    def persist_bytes(
        self,
        content: bytes,
        *,
        series_id: str,
        job_id: str,
        filename: str,
        kind: str,
        duration_seconds: float | None = None,
        metadata: dict[str, object] | None = None,
    ) -> FinalArtifact:
        if not content:
            raise ValueError("Cannot persist an empty final artifact")
        directory = self.root / self._safe(series_id) / "final-episodes" / self._safe(job_id)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / self._safe_filename(filename)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        relative = destination.resolve().relative_to(self.root)
        return FinalArtifact(
            kind=kind,
            url=f"/artifacts/{relative.as_posix()}",
            filename=destination.name,
            storage_path=str(destination),
            mime_type=_MIME_TYPES.get(destination.suffix.lower(), "application/octet-stream"),
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            duration_seconds=duration_seconds,
            metadata=metadata or {},
        )

    def persist_file(
        self,
        source_path: str,
        *,
        series_id: str,
        job_id: str,
        filename: str,
        kind: str,
        duration_seconds: float | None = None,
        metadata: dict[str, object] | None = None,
    ) -> FinalArtifact:
        return self.persist_bytes(
            Path(source_path).read_bytes(),
            series_id=series_id,
            job_id=job_id,
            filename=filename,
            kind=kind,
            duration_seconds=duration_seconds,
            metadata=metadata,
        )

    @staticmethod
    def _safe(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
        if not cleaned:
            raise ValueError("Final artifact path identifier is empty")
        return cleaned[:200]

    @classmethod
    def _safe_filename(cls, filename: str) -> str:
        source = Path(filename)
        stem = cls._safe(source.stem)
        suffix = source.suffix.lower()
        if suffix not in _MIME_TYPES:
            raise ValueError("Unsupported final artifact extension")
        return f"{stem}{suffix}"
