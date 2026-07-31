from typing import Protocol

from packages.sound.models import RenderedSoundAsset, SoundCueSpec, SoundProviderHealth


class SoundProvider(Protocol):
    name: str

    async def health(self) -> SoundProviderHealth: ...

    async def generate(self, spec: SoundCueSpec) -> RenderedSoundAsset: ...
