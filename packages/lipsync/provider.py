from typing import Protocol

from packages.lipsync.models import (
    LipSyncGenerationSpec,
    LipSyncProviderHealth,
    RenderedLipSyncVideo,
)


class LipSyncProvider(Protocol):
    async def health(self) -> LipSyncProviderHealth: ...

    async def synthesize(self, spec: LipSyncGenerationSpec) -> RenderedLipSyncVideo: ...
