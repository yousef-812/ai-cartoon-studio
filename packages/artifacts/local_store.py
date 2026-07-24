import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx

from packages.images.errors import ImageProviderResponseError
from packages.images.models import GeneratedImage, ImageProviderResult


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
        self._validate_url(image.url)
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                follow_redirects=True,
                transport=self.transport,
            ) as client:
                response = await client.get(image.url)
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise ImageProviderResponseError(
                f"Could not persist generated image: {error}"
            ) from error

        content = response.content
        if not content:
            raise ImageProviderResponseError("Generated image response was empty")
        mime_type = response.headers.get("content-type", image.mime_type).split(";", 1)[0]
        suffix = self._suffix(image.filename, mime_type)
        directory = self.root / self._safe(series_id) / "visual-assets" / self._safe(asset_id)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{index:02d}{suffix}"
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        checksum = hashlib.sha256(content).hexdigest()
        return image.model_copy(
            update={
                "storage_path": str(destination),
                "checksum_sha256": checksum,
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

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ImageProviderResponseError("Generated image URL must use HTTP or HTTPS")
        if self.allowed_origin and self._origin(url) != self.allowed_origin:
            raise ImageProviderResponseError(
                "Generated image URL does not match the configured image provider origin"
            )

    @staticmethod
    def _origin(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"

    @staticmethod
    def _safe(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip(".-")
        if not cleaned:
            raise ImageProviderResponseError("Artifact path identifier is empty")
        return cleaned[:200]

    @staticmethod
    def _suffix(filename: str, mime_type: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
            return suffix
        return {
            "image/jpeg": ".jpg",
            "image/webp": ".webp",
        }.get(mime_type, ".png")
