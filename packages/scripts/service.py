from packages.common.errors import ConflictError, NotFoundError
from packages.scripts.models import (
    ScriptGenerationJobRead,
    ScriptGenerationRequest,
    ScriptJobStatus,
    ScriptReviewRequest,
)
from packages.scripts.repository import ScriptJobRepository


class ScriptJobService:
    def __init__(self, repository: ScriptJobRepository) -> None:
        self.repository = repository

    def create(
        self,
        series_id: str,
        story_job_id: str,
        request: ScriptGenerationRequest,
        provider: str,
        model: str,
    ) -> ScriptGenerationJobRead:
        return self.repository.create(series_id, story_job_id, request, provider, model)

    def get(self, job_id: str) -> ScriptGenerationJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Script generation job not found")
        return job

    def list_for_series(self, series_id: str) -> list[ScriptGenerationJobRead]:
        return self.repository.list_for_series(series_id)

    def fail(self, job_id: str, error: str) -> ScriptGenerationJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Script generation job not found")
        return failed

    def retry(self, job_id: str) -> ScriptGenerationJobRead:
        job = self.get(job_id)
        if job.status not in {ScriptJobStatus.FAILED, ScriptJobStatus.QUEUED}:
            raise ConflictError("Only failed or queued script jobs can be retried")
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Script generation job not found")
        return queued

    def review(self, job_id: str, request: ScriptReviewRequest) -> ScriptGenerationJobRead:
        job = self.get(job_id)
        if job.status is not ScriptJobStatus.SUCCEEDED:
            raise ConflictError("Only completed scripts can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Script generation job not found")
        return reviewed
