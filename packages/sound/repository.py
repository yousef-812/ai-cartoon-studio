from typing import Protocol

from packages.sound.models import (
    GeneratedSoundAsset,
    SoundMixJobRead,
    SoundMixJobSpec,
    SoundMixReviewRequest,
)
from packages.videos.models import GeneratedVideo


class SoundMixJobRepository(Protocol):
    def create_many(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[SoundMixJobSpec],
        provider: str,
    ) -> list[SoundMixJobRead]: ...

    def get(self, job_id: str) -> SoundMixJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[SoundMixJobRead]: ...

    def list_for_direction(self, direction_job_id: str) -> list[SoundMixJobRead]: ...

    def mark_queued(self, job_id: str) -> SoundMixJobRead | None: ...

    def mark_running(self, job_id: str) -> SoundMixJobRead | None: ...

    def complete(
        self,
        job_id: str,
        assets: list[GeneratedSoundAsset],
        video: GeneratedVideo,
    ) -> SoundMixJobRead | None: ...

    def fail(self, job_id: str, error: str) -> SoundMixJobRead | None: ...

    def review(
        self,
        job_id: str,
        request: SoundMixReviewRequest,
    ) -> SoundMixJobRead | None: ...
