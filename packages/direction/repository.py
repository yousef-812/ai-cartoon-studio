from typing import Protocol

from packages.direction.models import (
    DirectionGenerationJobRead,
    DirectionGenerationRequest,
    DirectionReviewRequest,
    EpisodeDirection,
)


class DirectionJobRepository(Protocol):
    def create(
        self,
        series_id: str,
        script_job_id: str,
        request: DirectionGenerationRequest,
        provider: str,
        model: str,
    ) -> DirectionGenerationJobRead: ...

    def get(self, job_id: str) -> DirectionGenerationJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[DirectionGenerationJobRead]: ...

    def mark_running(self, job_id: str) -> DirectionGenerationJobRead | None: ...

    def mark_queued(self, job_id: str) -> DirectionGenerationJobRead | None: ...

    def complete(
        self, job_id: str, result: EpisodeDirection
    ) -> DirectionGenerationJobRead | None: ...

    def fail(self, job_id: str, error: str) -> DirectionGenerationJobRead | None: ...

    def review(
        self, job_id: str, request: DirectionReviewRequest
    ) -> DirectionGenerationJobRead | None: ...
