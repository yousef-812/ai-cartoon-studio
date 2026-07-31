import json
from pathlib import Path

import httpx

from packages.lipsync.errors import (
    LipSyncProviderResponseError,
    LipSyncProviderUnavailableError,
)
from packages.lipsync.models import (
    LipSyncGenerationSpec,
    LipSyncProviderHealth,
    RenderedLipSyncVideo,
)


class SelfHostedLipSyncProvider:
    name = "local-lip-sync-http"

    def __init__(
        self,
        *,
        base_url: str,
        endpoint_path: str = "/v1/lip-sync",
        api_key: str = "",
        timeout_seconds: float = 1200,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint_path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def health(self) -> LipSyncProviderHealth:
        if not self.base_url:
            return LipSyncProviderHealth(
                available=False,
                provider=self.name,
                detail="LIP_SYNC_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.get(f"{self.base_url}/health", headers=self._headers())
                response.raise_for_status()
            return LipSyncProviderHealth(
                available=True,
                provider=self.name,
                detail="Self-hosted lip-sync endpoint is ready.",
            )
        except httpx.HTTPError as error:
            return LipSyncProviderHealth(
                available=False,
                provider=self.name,
                detail=str(error),
            )

    async def synthesize(self, spec: LipSyncGenerationSpec) -> RenderedLipSyncVideo:
        if not self.base_url:
            raise LipSyncProviderUnavailableError("LIP_SYNC_BASE_URL is not configured")
        video_path = Path(spec.input_video_path)
        if not video_path.is_file():
            raise LipSyncProviderResponseError("Lip-sync input video file is missing")

        opened_files = []
        try:
            files: list[tuple[str, tuple[str, object, str]]] = []
            video_handle = video_path.open("rb")
            opened_files.append(video_handle)
            files.append(("video", (video_path.name, video_handle, "video/mp4")))

            manifest_segments: list[dict[str, object]] = []
            for index, segment in enumerate(spec.segments):
                audio_path = Path(segment.audio_path)
                if not audio_path.is_file():
                    raise LipSyncProviderResponseError(
                        f"Lip-sync audio file is missing for {segment.character_name}"
                    )
                audio_handle = audio_path.open("rb")
                opened_files.append(audio_handle)
                field_name = f"audio_{index}"
                files.append((field_name, (audio_path.name, audio_handle, "application/octet-stream")))
                manifest_segments.append(
                    {
                        **segment.model_dump(mode="json", exclude={"audio_path"}),
                        "audio_field": field_name,
                    }
                )

            manifest = {
                "scene_number": spec.scene_number,
                "shot_number": spec.shot_number,
                "duration_seconds": spec.duration_seconds,
                "model": spec.model,
                "quality": spec.quality,
                "face_detection_confidence": spec.face_detection_confidence,
                "preserve_original_audio": spec.preserve_original_audio,
                "constraints": spec.constraints,
                "segments": manifest_segments,
                "metadata": spec.metadata,
            }
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.post(
                        f"{self.base_url}{self.endpoint_path}",
                        headers=self._headers(),
                        data={"manifest": json.dumps(manifest)},
                        files=files,
                    )
                    response.raise_for_status()
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
                raise LipSyncProviderUnavailableError(str(error)) from error
            except httpx.HTTPStatusError as error:
                if error.response.status_code >= 500:
                    raise LipSyncProviderUnavailableError(str(error)) from error
                raise LipSyncProviderResponseError(str(error)) from error
            except httpx.HTTPError as error:
                raise LipSyncProviderResponseError(str(error)) from error

            content_type = response.headers.get("content-type", "video/mp4").split(";", 1)[0]
            supported_types = {
                "video/mp4",
                "video/webm",
                "video/quicktime",
                "video/x-matroska",
            }
            if content_type not in supported_types:
                raise LipSyncProviderResponseError(
                    f"Lip-sync endpoint returned unsupported content type: {content_type}"
                )
            if not response.content:
                raise LipSyncProviderResponseError("Lip-sync endpoint returned an empty video")
            suffix = {
                "video/webm": ".webm",
                "video/quicktime": ".mov",
                "video/x-matroska": ".mkv",
            }.get(content_type, ".mp4")
            return RenderedLipSyncVideo(
                content=response.content,
                filename=f"scene-{spec.scene_number}-shot-{spec.shot_number}-lip-sync{suffix}",
                mime_type=content_type,
                duration_seconds=spec.duration_seconds,
                metadata={"segments": len(spec.segments), **spec.metadata},
            )
        finally:
            for handle in opened_files:
                handle.close()
