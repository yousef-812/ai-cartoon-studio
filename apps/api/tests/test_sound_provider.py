import asyncio
import json

import httpx

from packages.sound.http_provider import SelfHostedSoundProvider
from packages.sound.models import SoundCueKind, SoundCueSpec


def test_sound_provider_posts_generation_request() -> None:
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/audio/generate"
        observed.update(json.loads(request.read().decode("utf-8")))
        return httpx.Response(
            200,
            content=b"generated-wave",
            headers={"content-type": "audio/wav"},
        )

    provider = SelfHostedSoundProvider(
        base_url="https://sound.example",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )
    rendered = asyncio.run(
        provider.generate(
            SoundCueSpec(
                key="scene:1:shot:1:ambience",
                kind=SoundCueKind.AMBIENCE,
                prompt="Quiet workshop room tone with a distant electrical hum.",
                duration_seconds=4,
                loop=True,
                model="local-audio-model",
            )
        )
    )

    assert observed["kind"] == "ambience"
    assert observed["duration_seconds"] == 4
    assert observed["loop"] is True
    assert rendered.content == b"generated-wave"
    assert rendered.mime_type == "audio/wav"
