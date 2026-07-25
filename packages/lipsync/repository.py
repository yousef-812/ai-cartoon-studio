from typing import Protocol

from packages.lipsync.models import (
    LipSyncJobRead,
    LipSyncReviewRequest,
    LipSyncShotSpec,
)
from packages.videos.models import VideoProviderResult


class LipSyncJobRepository(Protocol):
    def create_many(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[LipSyncShotSpec],
        provider: str,
    ) -> list[LipSyncJobRead]: ...

    def get(self, job_id: str) -> LipSyncJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[LipSyncJobRead]: ...

    def list_for_direction(self, direction_job_id: str) -> list[LipSyncJobRead]: ...

    def mark_queued(self, job_id: str) -> LipSyncJobRead | None: ...

    def mark_running(self, job_id: str) -> LipSyncJobRead | None: ...

    def complete(self, job_id: str, result: VideoProviderResult) -> LipSyncJobRead | None: ...

    def fail(self, job_id: str, error: str) -> LipSyncJobRead | None: ...

    def review(
        self,
        job_id: str,
        request: LipSyncReviewRequest,
    ) -> LipSyncJobRead | None: ...
