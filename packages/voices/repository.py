from typing import Protocol

from packages.audio.models import GeneratedAudio
from packages.voices.models import VoiceJobRead, VoiceLineSpec, VoiceReviewRequest


class VoiceJobRepository(Protocol):
    def create_many(
        self,
        series_id: str,
        script_job_id: str,
        specs: list[VoiceLineSpec],
        provider: str,
    ) -> list[VoiceJobRead]: ...

    def get(self, job_id: str) -> VoiceJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[VoiceJobRead]: ...

    def list_for_script(self, script_job_id: str) -> list[VoiceJobRead]: ...

    def mark_queued(self, job_id: str) -> VoiceJobRead | None: ...

    def mark_running(self, job_id: str) -> VoiceJobRead | None: ...

    def complete(self, job_id: str, audio: GeneratedAudio) -> VoiceJobRead | None: ...

    def fail(self, job_id: str, error: str) -> VoiceJobRead | None: ...

    def review(self, job_id: str, request: VoiceReviewRequest) -> VoiceJobRead | None: ...
