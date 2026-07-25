from pathlib import Path

from packages.animations.models import (
    AnimationJobStatus,
    AnimationReviewStatus,
)
from packages.animations.repository import AnimationJobRepository
from packages.common.errors import ConflictError, NotFoundError
from packages.lipsync.models import LipSyncJobStatus, LipSyncReviewStatus
from packages.lipsync.repository import LipSyncJobRepository
from packages.sound.models import (
    SoundMixJobRead,
    SoundMixJobSpec,
    SoundMixJobStatus,
    SoundMixReviewRequest,
)
from packages.sound.repository import SoundMixJobRepository


class SoundMixJobService:
    def __init__(
        self,
        repository: SoundMixJobRepository,
        animation_repository: AnimationJobRepository,
        lip_sync_repository: LipSyncJobRepository,
    ) -> None:
        self.repository = repository
        self.animation_repository = animation_repository
        self.lip_sync_repository = lip_sync_repository

    def create_plan(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[SoundMixJobSpec],
        provider: str,
    ) -> list[SoundMixJobRead]:
        return self.repository.create_many(series_id, direction_job_id, specs, provider)

    def get(self, job_id: str) -> SoundMixJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Sound mix job not found")
        return job

    def list_for_series(self, series_id: str) -> list[SoundMixJobRead]:
        return self.repository.list_for_series(series_id)

    def list_for_direction(self, direction_job_id: str) -> list[SoundMixJobRead]:
        return self.repository.list_for_direction(direction_job_id)

    def queue(self, job_id: str) -> SoundMixJobRead:
        job = self.get(job_id)
        if job.status not in {SoundMixJobStatus.PLANNED, SoundMixJobStatus.FAILED}:
            raise ConflictError("Only planned or failed sound mix jobs can be queued")
        self._validate_source(job)
        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Sound mix job not found")
        return queued

    def fail(self, job_id: str, error: str) -> SoundMixJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Sound mix job not found")
        return failed

    def review(
        self,
        job_id: str,
        request: SoundMixReviewRequest,
    ) -> SoundMixJobRead:
        job = self.get(job_id)
        if job.status != SoundMixJobStatus.SUCCEEDED:
            raise ConflictError("Only completed sound mixes can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Sound mix job not found")
        return reviewed

    def _validate_source(self, job: SoundMixJobRead) -> None:
        if job.source_job_type == "lip_sync":
            source = self.lip_sync_repository.get(job.source_job_id)
            if source is None:
                raise NotFoundError("Lip-sync source job not found")
            if source.status != LipSyncJobStatus.SUCCEEDED:
                raise ConflictError("Lip-sync source must finish successfully")
            if source.review_status != LipSyncReviewStatus.APPROVED:
                raise ConflictError("Approve the lip-sync source before sound mixing")
            videos = source.videos
        else:
            source = self.animation_repository.get(job.source_job_id)
            if source is None:
                raise NotFoundError("Animation source job not found")
            if source.status != AnimationJobStatus.SUCCEEDED:
                raise ConflictError("Animation source must finish successfully")
            if source.review_status != AnimationReviewStatus.APPROVED:
                raise ConflictError("Approve the animation source before sound mixing")
            videos = source.videos
        if not videos or not videos[0].storage_path:
            raise ConflictError("Sound mix source is not stored permanently")
        if not Path(videos[0].storage_path).is_file():
            raise ConflictError("Stored sound mix source file is missing")
