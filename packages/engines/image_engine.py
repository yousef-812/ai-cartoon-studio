from typing import Any

from packages.engines.base import GenerationResult, MediaEngine


class ImageEngine(MediaEngine):
    capability = "image"

    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        raise NotImplementedError("Configure an image generation provider.")
