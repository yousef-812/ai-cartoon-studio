from typing import Any

from packages.engines.base import GenerationResult, MediaEngine


class SoundEngine(MediaEngine):
    capability = "sound"

    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        raise NotImplementedError("Configure licensed sound and music sources.")
