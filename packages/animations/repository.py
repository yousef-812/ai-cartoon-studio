from typing import Protocol

from packages.animations.models import (
    AnimatedShotSpec,
    AnimationJobRead,
    AnimationReviewRequest,
)
from packages.videos.models import VideoProviderResult


class AnimationJobRepository(Protocol):
    def create_many(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[AnimatedShotSpec],
        provider: str,
    ) -> list[AnimationJobRead]: ...

    def get(self, job_id: str) -> AnimationJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[AnimationJobRead]: ...

    def list_for_direction(self, direction_job_id: str) -> list[AnimationJobRead]: ...

    def mark_queued(self, job_id: str) -> AnimationJobRead | None: ...

    def mark_running(self, job_id: str) -> AnimationJobRead | None: ...

    def set_provider_job(self, job_id: str, provider_job_id: str) -> AnimationJobRead | None: ...

    def complete(self, job_id: str, result: VideoProviderResult) -> AnimationJobRead | None: ...

    def fail(self, job_id: str, error: str) -> AnimationJobRead | None: ...

    def review(
        self,
        job_id: str,
        request: AnimationReviewRequest,
    ) -> AnimationJobRead | None: ...
