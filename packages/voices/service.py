from packages.common.errors import ConflictError, NotFoundError
from packages.voices.models import (
    VoiceJobRead,
    VoiceJobStatus,
    VoiceLineSpec,
    VoiceReviewRequest,
)
from packages.voices.repository import VoiceJobRepository


class VoiceJobService:
    def __init__(self, repository: VoiceJobRepository) -> None:
        self.repository = repository

    def create_plan(
        self,
        series_id: str,
        script_job_id: str,
        specs: list[VoiceLineSpec],
        provider: str,
    ) -> list[VoiceJobRead]:
        return self.repository.create_many(series_id, script_job_id, specs, provider)

    def get(self, job_id: str) -> VoiceJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Voice job not found")
        return job

    def list_for_series(self, series_id: str) -> list[VoiceJobRead]:
        return self.repository.list_for_series(series_id)

    def list_for_script(self, script_job_id: str) -> list[VoiceJobRead]:
        return self.repository.list_for_script(script_job_id)

    def queue(self, job_id: str) -> VoiceJobRead:
        job = self.get(job_id)
        if job.status not in {VoiceJobStatus.PLANNED, VoiceJobStatus.FAILED}:
            raise ConflictError("Only planned or failed voice jobs can be queued")
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Voice job not found")
        return queued

    def fail(self, job_id: str, error: str) -> VoiceJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Voice job not found")
        return failed

    def review(self, job_id: str, request: VoiceReviewRequest) -> VoiceJobRead:
        job = self.get(job_id)
        if job.status != VoiceJobStatus.SUCCEEDED:
            raise ConflictError("Only completed voice lines can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Voice job not found")
        return reviewed
