from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import (
    DirectionGenerationJobRead,
    DirectionGenerationRequest,
    DirectionJobStatus,
    DirectionReviewRequest,
)
from packages.direction.repository import DirectionJobRepository


class DirectionJobService:
    def __init__(self, repository: DirectionJobRepository) -> None:
        self.repository = repository

    def create(
        self,
        series_id: str,
        script_job_id: str,
        request: DirectionGenerationRequest,
        provider: str,
        model: str,
    ) -> DirectionGenerationJobRead:
        return self.repository.create(series_id, script_job_id, request, provider, model)

    def get(self, job_id: str) -> DirectionGenerationJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Direction generation job not found")
        return job

    def list_for_series(self, series_id: str) -> list[DirectionGenerationJobRead]:
        return self.repository.list_for_series(series_id)

    def fail(self, job_id: str, error: str) -> DirectionGenerationJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Direction generation job not found")
        return failed

    def retry(self, job_id: str) -> DirectionGenerationJobRead:
        job = self.get(job_id)
        if job.status not in {DirectionJobStatus.FAILED, DirectionJobStatus.QUEUED}:
            raise ConflictError("Only failed or queued direction jobs can be retried")
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Direction generation job not found")
        return queued

    def review(
        self, job_id: str, request: DirectionReviewRequest
    ) -> DirectionGenerationJobRead:
        job = self.get(job_id)
        if job.status != DirectionJobStatus.SUCCEEDED:
            raise ConflictError("Only completed direction plans can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Direction generation job not found")
        return reviewed
