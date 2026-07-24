from typing import Any

from packages.engines.base import GenerationResult, MediaEngine


class VoiceEngine(MediaEngine):
    capability = "voice"

    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        raise NotImplementedError("Configure a licensed voice provider.")
