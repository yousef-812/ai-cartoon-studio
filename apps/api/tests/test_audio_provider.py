import asyncio

import httpx

from packages.audio.models import SpeechSynthesisSpec
from packages.audio.openai_compatible import OpenAICompatibleAudioProvider


def test_audio_provider_sends_voice_context_and_returns_binary_audio() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/audio/speech":
            observed.update(request.read() and __import__("json").loads(request.content))
            return httpx.Response(
                200,
                content=b"RIFF-fake-wave",
                headers={"content-type": "audio/wav"},
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    provider = OpenAICompatibleAudioProvider(
        base_url="https://voice.example",
        model="local-tts",
        transport=httpx.MockTransport(handler),
    )
    audio = asyncio.run(
        provider.synthesize(
            SpeechSynthesisSpec(
                text="The cloud engine is finally stable.",
                voice_id="mira-main",
                language="en",
                emotion="relieved",
                delivery="soft and smiling",
                speed=1.05,
                pitch=1.0,
                target_duration_seconds=2.4,
            )
        )
    )

    assert observed["voice"] == "mira-main"
    assert observed["emotion"] == "relieved"
    assert observed["delivery"] == "soft and smiling"
    assert audio.content == b"RIFF-fake-wave"
    assert audio.mime_type == "audio/wav"
    assert audio.duration_seconds == 2.4
