import asyncio
import json

import httpx

from packages.llm.models import LLMMessage
from packages.llm.openai_compatible import OpenAICompatibleLLMProvider


def test_openai_compatible_provider_health_and_json_generation() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "local-model"}]})
        payload = json.loads(request.content)
        assert payload["model"] == "local-model"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "<think>Check the requested schema before answering.</think>\n"
                                '```json\n{"title": "A valid story"}\n```'
                            )
                        }
                    }
                ]
            },
        )

    provider = OpenAICompatibleLLMProvider(
        base_url="https://local.test/v1",
        model="local-model",
        api_key="secret",
        transport=httpx.MockTransport(handler),
    )

    health = asyncio.run(provider.health())
    result = asyncio.run(
        provider.generate_json([LLMMessage(role="user", content="Return JSON")])
    )

    assert health.available is True
    assert result == {"title": "A valid story"}
