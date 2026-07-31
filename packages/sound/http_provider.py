import httpx

from packages.sound.errors import (
    SoundProviderResponseError,
    SoundProviderUnavailableError,
)
from packages.sound.models import RenderedSoundAsset, SoundCueSpec, SoundProviderHealth


class SelfHostedSoundProvider:
    name = "local-sound-http"

    def __init__(
        self,
        *,
        base_url: str,
        endpoint_path: str = "/v1/audio/generate",
        api_key: str = "",
        timeout_seconds: float = 600,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.endpoint_path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "audio/wav,audio/mpeg,audio/flac,audio/ogg"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health(self) -> SoundProviderHealth:
        if not self.base_url:
            return SoundProviderHealth(
                available=False,
                provider=self.name,
                detail="SOUND_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.get(f"{self.base_url}/health", headers=self._headers())
                response.raise_for_status()
            return SoundProviderHealth(
                available=True,
                provider=self.name,
                detail="Self-hosted sound generation endpoint is ready.",
            )
        except httpx.HTTPError as error:
            return SoundProviderHealth(
                available=False,
                provider=self.name,
                detail=str(error),
            )

    async def generate(self, spec: SoundCueSpec) -> RenderedSoundAsset:
        if not self.base_url:
            raise SoundProviderUnavailableError("SOUND_BASE_URL is not configured")
        payload = {
            "kind": spec.kind.value,
            "prompt": spec.prompt,
            "duration_seconds": spec.duration_seconds,
            "model": spec.model,
            "seed": spec.seed,
            "loop": spec.loop,
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
                    json=payload,
                )
            if response.status_code >= 500:
                raise SoundProviderUnavailableError(
                    f"Sound provider returned HTTP {response.status_code}"
                )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise SoundProviderUnavailableError(str(error)) from error
        except httpx.HTTPStatusError as error:
            raise SoundProviderResponseError(str(error)) from error

        mime_type = response.headers.get("content-type", "audio/wav").split(";", 1)[0]
        allowed = {
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/flac": ".flac",
            "audio/ogg": ".ogg",
        }
        if mime_type not in allowed:
            raise SoundProviderResponseError(
                f"Sound endpoint returned unsupported content type: {mime_type}"
            )
        if not response.content:
            raise SoundProviderResponseError("Sound endpoint returned empty audio")
        return RenderedSoundAsset(
            content=response.content,
            filename=f"{spec.kind.value}{allowed[mime_type]}",
            mime_type=mime_type,
            duration_seconds=spec.duration_seconds,
            metadata={"cue_key": spec.key, "kind": spec.kind.value, **spec.metadata},
        )
