import asyncio

import httpx

from packages.audio.errors import (
    AudioProviderResponseError,
    AudioProviderUnavailableError,
)
from packages.audio.models import AudioProviderHealth, SpeechSynthesisSpec, SynthesizedAudio


class OpenAICompatibleAudioProvider:
    """Connect to a self-hosted TTS server exposing an OpenAI-compatible speech endpoint."""

    name = "local-openai-compatible-tts"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_seconds: float = 300,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.transport = transport

    def _endpoint(self, path: str) -> str:
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/{path.lstrip('/')}"
        return f"{self.base_url}/v1/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def health(self) -> AudioProviderHealth:
        if not self.base_url:
            return AudioProviderHealth(
                available=False,
                provider=self.name,
                model=self.model,
                detail="VOICE_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.get(self._endpoint("models"), headers=self._headers())
                response.raise_for_status()
            return AudioProviderHealth(
                available=True,
                provider=self.name,
                model=self.model,
                detail="Self-hosted speech endpoint is reachable.",
            )
        except (httpx.HTTPError, ValueError) as error:
            return AudioProviderHealth(
                available=False,
                provider=self.name,
                model=self.model,
                detail=str(error),
            )

    async def synthesize(self, spec: SpeechSynthesisSpec) -> SynthesizedAudio:
        if not self.base_url:
            raise AudioProviderUnavailableError("VOICE_BASE_URL is not configured")
        response_format = spec.response_format
        payload: dict[str, object] = {
            "model": spec.model or self.model,
            "input": spec.text,
            "voice": spec.voice_id,
            "response_format": response_format,
            "speed": spec.speed,
            "language": spec.language,
            "emotion": spec.emotion,
            "delivery": spec.delivery,
            "pitch": spec.pitch,
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self.timeout_seconds,
                    transport=self.transport,
                ) as client:
                    response = await client.post(
                        self._endpoint("audio/speech"),
                        headers=self._headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                content = response.content
                if not content:
                    raise AudioProviderResponseError("Speech provider returned empty audio")
                mime_type = response.headers.get(
                    "content-type",
                    self._mime_type(response_format),
                ).split(";", 1)[0]
                return SynthesizedAudio(
                    content=content,
                    filename=f"speech.{response_format}",
                    mime_type=mime_type,
                    duration_seconds=spec.target_duration_seconds,
                    metadata=spec.metadata,
                )
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code < 500:
                    raise AudioProviderResponseError(str(error)) from error
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
                last_error = error
            if attempt < self.max_retries:
                await asyncio.sleep(min(2**attempt, 8))
        raise AudioProviderUnavailableError(str(last_error or "Speech request failed"))

    @staticmethod
    def _mime_type(response_format: str) -> str:
        return {
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "opus": "audio/ogg",
        }.get(response_format, "audio/wav")
