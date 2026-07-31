import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from packages.audio.models import GeneratedAudio, SynthesizedAudio
from packages.images.errors import ImageProviderResponseError
from packages.images.models import GeneratedImage, ImageProviderResult
from packages.videos.errors import VideoProviderResponseError
from packages.videos.models import GeneratedVideo, VideoProviderResult


class LocalArtifactStore:
    def __init__(
        self,
        root_path: str,
        *,
        allowed_base_url: str = "",
        timeout_seconds: float = 120,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.root = Path(root_path).resolve()
        self.allowed_origin = self._origin(allowed_base_url) if allowed_base_url else ""
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def persist_image(
        self,
        image: GeneratedImage,
        *,
        series_id: str,
        asset_id: str,
        index: int,
    ) -> GeneratedImage:
        if image.storage_path:
            return image
        try:
            content, mime_type = await self._download(image.url, image.mime_type)
        except (httpx.HTTPError, ValueError) as error:
            raise ImageProviderResponseError(
                f"Could not persist generated image: {error}"
            ) from error
        suffix = self._image_suffix(image.filename, mime_type)
        destination = self._write(
            content,
            self.root / self._safe(series_id) / "visual-assets" / self._safe(asset_id),
            f"{index:02d}{suffix}",
        )
        return image.model_copy(
            update={
                "url": self._public_url(destination),
                "storage_path": str(destination),
                "checksum_sha256": hashlib.sha256(content).hexdigest(),
                "mime_type": mime_type,
                "size_bytes": len(content),
            }
        )

    async def persist_result(
        self,
        result: ImageProviderResult,
        *,
        series_id: str,
        asset_id: str,
    ) -> ImageProviderResult:
        images = [
            await self.persist_image(
                image,
                series_id=series_id,
                asset_id=asset_id,
                index=index,
            )
            for index, image in enumerate(result.images, start=1)
        ]
        return result.model_copy(update={"images": images})

    async def persist_video(
        self,
        video: GeneratedVideo,
        *,
        series_id: str,
        animation_id: str,
        index: int,
    ) -> GeneratedVideo:
        if video.storage_path:
            return video
        try:
            content, mime_type = await self._download(video.url, video.mime_type)
        except (httpx.HTTPError, ValueError) as error:
            raise VideoProviderResponseError(
                f"Could not persist generated video: {error}"
            ) from error
        suffix = self._video_suffix(video.filename, mime_type)
        destination = self._write(
            content,
            self.root / self._safe(series_id) / "animated-shots" / self._safe(animation_id),
            f"{index:02d}{suffix}",
        )
        return video.model_copy(
            update={
                "url": self._public_url(destination),
                "storage_path": str(destination),
                "checksum_sha256": hashlib.sha256(content).hexdigest(),
                "mime_type": mime_type,
                "size_bytes": len(content),
            }
        )

    async def persist_video_result(
        self,
        result: VideoProviderResult,
        *,
        series_id: str,
        animation_id: str,
    ) -> VideoProviderResult:
        videos = [
            await self.persist_video(
                video,
                series_id=series_id,
                animation_id=animation_id,
                index=index,
            )
            for index, video in enumerate(result.videos, start=1)
        ]
        return result.model_copy(update={"videos": videos})

    def persist_audio(
        self,
        audio: SynthesizedAudio,
        *,
        series_id: str,
        voice_job_id: str,
    ) -> GeneratedAudio:
        suffix = self._audio_suffix(audio.filename, audio.mime_type)
        destination = self._write(
            audio.content,
            self.root / self._safe(series_id) / "voice-lines" / self._safe(voice_job_id),
            f"voice{suffix}",
        )
        return GeneratedAudio(
            url=self._public_url(destination),
            filename=destination.name,
            storage_path=str(destination),
            mime_type=audio.mime_type,
            size_bytes=len(audio.content),
            checksum_sha256=hashlib.sha256(audio.content).hexdigest(),
            duration_seconds=audio.duration_seconds,
            sample_rate=audio.sample_rate,
            channels=audio.channels,
            metadata=audio.metadata,
        )

    async def _download(self, url: str, fallback_mime: str) -> tuple[bytes, str]:
        self._validate_url(url)
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            transport=self.transport,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
        content = response.content
        if not content:
            raise ValueError("Generated artifact response was empty")
        mime_type = response.headers.get("content-type", fallback_mime).split(";", 1)[0]
        return content, mime_type

    @staticmethod
    def _write(content: bytes, directory: Path, filename: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        return destination

    def _public_url(self, destination: Path) -> str:
        relative = destination.resolve().relative_to(self.root)
        return f"/artifacts/{relative.as_posix()}"

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Generated artifact URL must use HTTP or HTTPS")
        if self.allowed_origin and self._origin(url) != self.allowed_origin:
            raise ValueError(
                "Generated artifact URL does not match the configured provider origin"
            )

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    @staticmethod
    def _safe(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
        if not cleaned:
            raise ValueError("Artifact path identifier is empty")
        return cleaned[:200]

    @staticmethod
    def _image_suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            return suffix
        return {
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }.get(mime_type, ".png")

    @staticmethod
    def _video_suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".mp4", ".webm", ".mov", ".mkv"}:
            return suffix
        return {
            "video/webm": ".webm",
            "video/quicktime": ".mov",
            "video/x-matroska": ".mkv",
        }.get(mime_type, ".mp4")

    @staticmethod
    def _audio_suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".wav", ".mp3", ".flac", ".opus", ".ogg"}:
            return suffix
        return {
            "audio/mpeg": ".mp3",
            "audio/flac": ".flac",
            "audio/ogg": ".opus",
        }.get(mime_type, ".wav")
