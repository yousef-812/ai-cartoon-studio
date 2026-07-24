from packages.common.errors import ConflictError, NotFoundError
from packages.stories.models import (
    StoryGenerationJobRead,
    StoryGenerationRequest,
    StoryJobStatus,
    StoryReviewRequest,
)
from packages.stories.repository import StoryJobRepository


class StoryJobService:
    def __init__(self, repository: StoryJobRepository) -> None:
        self.repository = repository

    def create(
        self,
        series_id: str,
        request: StoryGenerationRequest,
        provider: str,
        model: str,
    ) -> StoryGenerationJobRead:
        return self.repository.create(series_id, request, provider, model)

    def get(self, job_id: str) -> StoryGenerationJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Story generation job not found")
        return job

    def list_for_series(self, series_id: str) -> list[StoryGenerationJobRead]:
        return self.repository.list_for_series(series_id)

    def fail(self, job_id: str, error: str) -> StoryGenerationJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Story generation job not found")
        return failed

    def retry(self, job_id: str) -> StoryGenerationJobRead:
        job = self.get(job_id)
        if job.status not in {StoryJobStatus.FAILED, StoryJobStatus.QUEUED}:
            raise ConflictError("Only failed or queued story jobs can be retried")
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Story generation job not found")
        return queued

    def review(self, job_id: str, request: StoryReviewRequest) -> StoryGenerationJobRead:
        job = self.get(job_id)
        if job.status is not StoryJobStatus.SUCCEEDED:
            raise ConflictError("Only completed stories can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Story generation job not found")
        return reviewed
