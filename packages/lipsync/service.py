from pathlib import Path

from packages.animations.models import AnimationJobStatus, AnimationReviewStatus
from packages.animations.repository import AnimationJobRepository
from packages.common.errors import ConflictError, NotFoundError
from packages.lipsync.models import (
    LipSyncJobRead,
    LipSyncJobStatus,
    LipSyncReviewRequest,
    LipSyncShotSpec,
)
from packages.lipsync.repository import LipSyncJobRepository
from packages.voices.models import VoiceJobStatus, VoiceReviewStatus
from packages.voices.repository import VoiceJobRepository


class LipSyncJobService:
    def __init__(
        self,
        repository: LipSyncJobRepository,
        animation_repository: AnimationJobRepository,
        voice_repository: VoiceJobRepository,
    ) -> None:
        self.repository = repository
        self.animation_repository = animation_repository
        self.voice_repository = voice_repository

    def create_plan(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[LipSyncShotSpec],
        provider: str,
    ) -> list[LipSyncJobRead]:
        return self.repository.create_many(series_id, direction_job_id, specs, provider)

    def get(self, job_id: str) -> LipSyncJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Lip-sync job not found")
        return job

    def list_for_series(self, series_id: str) -> list[LipSyncJobRead]:
        return self.repository.list_for_series(series_id)

    def list_for_direction(self, direction_job_id: str) -> list[LipSyncJobRead]:
        return self.repository.list_for_direction(direction_job_id)

    def queue(self, job_id: str) -> LipSyncJobRead:
        job = self.get(job_id)
        if job.status not in {LipSyncJobStatus.PLANNED, LipSyncJobStatus.FAILED}:
            raise ConflictError("Only planned or failed lip-sync jobs can be queued")

        animation = self.animation_repository.get(job.animation_job_id)
        if animation is None:
            raise NotFoundError("Source animation job not found")
        if animation.status != AnimationJobStatus.SUCCEEDED:
            raise ConflictError("Source animation must finish successfully before lip sync")
        if animation.review_status != AnimationReviewStatus.APPROVED:
            raise ConflictError("Approve the source animation before lip sync")
        if not animation.videos or not animation.videos[0].storage_path:
            raise ConflictError("Source animation is not stored permanently")
        if not Path(animation.videos[0].storage_path).is_file():
            raise ConflictError("Stored source animation file is missing")

        for segment in job.spec.generation.segments:
            voice = self.voice_repository.get(segment.voice_job_id)
            if voice is None:
                raise NotFoundError("Lip-sync voice job not found")
            if voice.status != VoiceJobStatus.SUCCEEDED:
                raise ConflictError("Every voice line must finish successfully before lip sync")
            if voice.review_status != VoiceReviewStatus.APPROVED:
                raise ConflictError("Approve every voice line before lip sync")
            if voice.audio is None or not voice.audio.storage_path:
                raise ConflictError("Voice line is not stored permanently")
            if not Path(voice.audio.storage_path).is_file():
                raise ConflictError("Stored voice line file is missing")

        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Lip-sync job not found")
        return queued

    def fail(self, job_id: str, error: str) -> LipSyncJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Lip-sync job not found")
        return failed

    def review(self, job_id: str, request: LipSyncReviewRequest) -> LipSyncJobRead:
        job = self.get(job_id)
        if job.status != LipSyncJobStatus.SUCCEEDED:
            raise ConflictError("Only completed lip-sync shots can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Lip-sync job not found")
        return reviewed
