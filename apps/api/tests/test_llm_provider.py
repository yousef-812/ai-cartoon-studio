import asyncio
import json

import httpx
import pytest

from packages.llm.errors import LLMResponseError
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
                        },
                        "finish_reason": "stop",
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


def test_openai_compatible_provider_rejects_truncated_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": '{"title": "An unfinished response'},
                        "finish_reason": "length",
                    }
                ]
            },
        )

    provider = OpenAICompatibleLLMProvider(
        base_url="https://local.test/v1",
        model="local-model",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(LLMResponseError, match="truncated"):
        asyncio.run(provider.generate_json([LLMMessage(role="user", content="Return JSON")]))
