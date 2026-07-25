import hashlib
import os
import re
from pathlib import Path
from uuid import uuid4

from packages.sound.models import (
    GeneratedSoundAsset,
    RenderedSoundAsset,
    RenderedSoundMix,
    SoundCueSpec,
)
from packages.videos.models import GeneratedVideo


class SoundArtifactStore:
    def __init__(self, root_path: str) -> None:
        self.root = Path(root_path).resolve()

    def persist_asset(
        self,
        rendered: RenderedSoundAsset,
        cue: SoundCueSpec,
        *,
        series_id: str,
        job_id: str,
        index: int,
    ) -> GeneratedSoundAsset:
        suffix = self._audio_suffix(rendered.filename, rendered.mime_type)
        destination = self._write(
            rendered.content,
            self.root / self._safe(series_id) / "sound-assets" / self._safe(job_id),
            f"{index:02d}-{self._safe(cue.kind.value)}{suffix}",
        )
        return GeneratedSoundAsset(
            id=str(uuid4()),
            cue_key=cue.key,
            kind=cue.kind,
            prompt=cue.prompt,
            url=self._public_url(destination),
            filename=destination.name,
            storage_path=str(destination),
            mime_type=rendered.mime_type,
            size_bytes=len(rendered.content),
            checksum_sha256=hashlib.sha256(rendered.content).hexdigest(),
            duration_seconds=rendered.duration_seconds or cue.duration_seconds,
            sample_rate=rendered.sample_rate,
            channels=rendered.channels,
            metadata={**rendered.metadata, "gain_db": cue.gain_db},
        )

    def persist_mix(
        self,
        rendered: RenderedSoundMix,
        *,
        series_id: str,
        job_id: str,
    ) -> GeneratedVideo:
        suffix = self._video_suffix(rendered.filename, rendered.mime_type)
        destination = self._write(
            rendered.content,
            self.root / self._safe(series_id) / "sound-mixes" / self._safe(job_id),
            f"mix{suffix}",
        )
        return GeneratedVideo(
            url=self._public_url(destination),
            filename=destination.name,
            storage_path=str(destination),
            mime_type=rendered.mime_type,
            size_bytes=len(rendered.content),
            checksum_sha256=hashlib.sha256(rendered.content).hexdigest(),
            duration_seconds=rendered.duration_seconds,
            metadata=rendered.metadata,
        )

    @staticmethod
    def _write(content: bytes, directory: Path, filename: str) -> Path:
        if not content:
            raise ValueError("Cannot persist an empty sound artifact")
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        return destination

    def _public_url(self, destination: Path) -> str:
        relative = destination.resolve().relative_to(self.root)
        return f"/artifacts/{relative.as_posix()}"

    @staticmethod
    def _safe(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
        if not cleaned:
            raise ValueError("Sound artifact path identifier is empty")
        return cleaned[:200]

    @staticmethod
    def _audio_suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".wav", ".mp3", ".flac", ".ogg", ".opus"}:
            return suffix
        return {
            "audio/mpeg": ".mp3",
            "audio/flac": ".flac",
            "audio/ogg": ".ogg",
        }.get(mime_type, ".wav")

    @staticmethod
    def _video_suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".mp4", ".mov", ".mkv", ".webm"}:
            return suffix
        return {
            "video/quicktime": ".mov",
            "video/x-matroska": ".mkv",
            "video/webm": ".webm",
        }.get(mime_type, ".mp4")
