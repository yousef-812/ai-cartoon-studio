from typing import Protocol

from packages.audio.models import AudioProviderHealth, SpeechSynthesisSpec, SynthesizedAudio


class AudioProvider(Protocol):
    name: str

    async def health(self) -> AudioProviderHealth: ...

    async def synthesize(self, spec: SpeechSynthesisSpec) -> SynthesizedAudio: ...
