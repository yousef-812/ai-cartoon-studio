import asyncio
import json
import re
from collections.abc import Mapping
from typing import Any

import httpx

from packages.llm.errors import LLMResponseError, LLMUnavailableError
from packages.llm.models import LLMHealth, LLMMessage


class OpenAICompatibleLLMProvider:
    """Connect to a self-hosted vLLM, llama.cpp, or compatible local endpoint."""

    name = "local-openai-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "",
        timeout_seconds: float = 300,
        max_retries: int = 2,
        use_json_response_format: bool = True,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.use_json_response_format = use_json_response_format
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

    async def health(self) -> LLMHealth:
        if not self.base_url:
            return LLMHealth(
                available=False,
                provider=self.name,
                model=self.model,
                detail="LLM_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(
                timeout=min(self.timeout_seconds, 30),
                transport=self.transport,
            ) as client:
                response = await client.get(self._endpoint("models"), headers=self._headers())
                response.raise_for_status()
            return LLMHealth(
                available=True,
                provider=self.name,
                model=self.model,
                detail="Self-hosted inference endpoint is reachable.",
            )
        except (httpx.HTTPError, ValueError) as error:
            return LLMHealth(
                available=False,
                provider=self.name,
                model=self.model,
                detail=str(error),
            )

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, object]:
        if not self.base_url:
            raise LLMUnavailableError("LLM_BASE_URL is not configured")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [message.model_dump() for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self.use_json_response_format:
            payload["response_format"] = {"type": "json_object"}

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self._request(payload)
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code == 400 and "response_format" in payload:
                    payload.pop("response_format", None)
                    continue
                if error.response.status_code < 500:
                    raise LLMResponseError(str(error)) from error
            except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
                last_error = error
            if attempt < self.max_retries:
                await asyncio.sleep(min(2**attempt, 8))

        raise LLMUnavailableError(str(last_error or "Local LLM request failed"))

    async def _request(self, payload: Mapping[str, Any]) -> dict[str, object]:
        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.post(
                self._endpoint("chat/completions"),
                headers=self._headers(),
                json=dict(payload),
            )
            response.raise_for_status()
            body = response.json()

        try:
            choice = body["choices"][0]
            content = choice["message"]["content"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, IndexError, TypeError) as error:
            raise LLMResponseError("LLM response did not contain message content") from error
        if finish_reason == "length":
            raise LLMResponseError(
                "LLM response was truncated because the max_tokens limit was reached"
            )
        if not isinstance(content, str):
            raise LLMResponseError("LLM message content must be text")
        return self._parse_json(content)

    @staticmethod
    def _parse_json(content: str) -> dict[str, object]:
        cleaned = content.strip()
        cleaned = re.sub(
            r"^(?:\s*<think>.*?</think>\s*)+",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
        if fence:
            cleaned = fence.group(1).strip()
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError as error:
            raise LLMResponseError(f"LLM returned invalid JSON: {error}") from error
        if not isinstance(value, dict):
            raise LLMResponseError("LLM JSON response must be an object")
        return value
