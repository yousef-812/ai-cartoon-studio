from typing import Protocol

from packages.llm.models import LLMHealth, LLMMessage


class LLMProvider(Protocol):
    name: str
    model: str

    async def health(self) -> LLMHealth: ...

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, object]: ...
