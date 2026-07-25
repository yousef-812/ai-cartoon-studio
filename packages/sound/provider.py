from typing import Protocol

from packages.sound.models import GeneratedSoundAsset, SoundCueSpec


class SoundProvider(Protocol):
    name: str

    async def health(self) -> dict[str, object]: ...

    async def generate(self, spec: SoundCueSpec) -> GeneratedSoundAsset: ...
