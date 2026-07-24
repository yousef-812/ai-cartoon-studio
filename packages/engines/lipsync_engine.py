from typing import Any

from packages.engines.base import GenerationResult, MediaEngine


class LipSyncEngine(MediaEngine):
    capability = "lip_sync"

    async def generate(self, payload: dict[str, Any]) -> GenerationResult:
        raise NotImplementedError("Configure a lip-sync provider.")
