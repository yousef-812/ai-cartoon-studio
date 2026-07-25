from pathlib import Path

from packages.common.errors import ConflictError, NotFoundError
from packages.finalization.models import (
    FinalizationJobRead,
    FinalizationJobSpec,
    FinalizationJobStatus,
    FinalizationReviewRequest,
)
from packages.finalization.repository import FinalizationJobRepository
from packages.sound.models import SoundMixJobStatus, SoundMixReviewStatus
from packages.sound.repository import SoundMixJobRepository


class FinalizationJobService:
    def __init__(
        self,
        repository: FinalizationJobRepository,
        sound_repository: SoundMixJobRepository,
    ) -> None:
        self.repository = repository
        self.sound_repository = sound_repository

    def create(self, series_id: str, spec: FinalizationJobSpec) -> FinalizationJobRead:
        if not spec.preflight_report.passed:
            raise ConflictError("Finalization preflight contains blocking errors")
        return self.repository.create(series_id, spec)

    def get(self, job_id: str) -> FinalizationJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Finalization job not found")
        return job

    def list_for_series(self, series_id: str) -> list[FinalizationJobRead]:
        return self.repository.list_for_series(series_id)

    def queue(self, job_id: str) -> FinalizationJobRead:
        job = self.get(job_id)
        if job.status not in {FinalizationJobStatus.PLANNED, FinalizationJobStatus.FAILED}:
            raise ConflictError("Only planned or failed finalization jobs can be queued")
        for shot in job.spec.shots:
            source = self.sound_repository.get(shot.sound_job_id)
            if source is None:
                raise NotFoundError("Sound mix source not found")
            if source.status != SoundMixJobStatus.SUCCEEDED:
                raise ConflictError("Every sound mix must still be successful")
            if source.review_status != SoundMixReviewStatus.APPROVED:
                raise ConflictError("Every sound mix must still be approved")
            if not source.videos or not Path(source.videos[0].storage_path).is_file():
                raise ConflictError("A final source media file is missing")
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Finalization job not found")
        return queued

    def review(
        self,
        job_id: str,
        request: FinalizationReviewRequest,
    ) -> FinalizationJobRead:
        job = self.get(job_id)
        if job.status != FinalizationJobStatus.SUCCEEDED:
            raise ConflictError("Only completed final episodes can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Finalization job not found")
        return reviewed
