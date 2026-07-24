from typing import Any

from packages.engines.base import GenerationResult, MediaEngine


class VideoEngine(MediaEngine):
    capability = "video"

    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        raise NotImplementedError("Configure a video generation provider.")
