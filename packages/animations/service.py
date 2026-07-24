from pathlib import Path

from packages.animations.models import (
    AnimatedShotSpec,
    AnimationJobRead,
    AnimationJobStatus,
    AnimationReviewRequest,
)
from packages.animations.repository import AnimationJobRepository
from packages.common.errors import ConflictError, NotFoundError
from packages.visuals.models import VisualAssetReviewStatus, VisualAssetStatus
from packages.visuals.repository import VisualAssetRepository


class AnimationJobService:
    def __init__(
        self,
        repository: AnimationJobRepository,
        visual_repository: VisualAssetRepository,
    ) -> None:
        self.repository = repository
        self.visual_repository = visual_repository

    def create_plan(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[AnimatedShotSpec],
        provider: str,
    ) -> list[AnimationJobRead]:
        return self.repository.create_many(series_id, direction_job_id, specs, provider)

    def get(self, job_id: str) -> AnimationJobRead:
        job = self.repository.get(job_id)
        if job is None:
            raise NotFoundError("Animation job not found")
        return job

    def list_for_series(self, series_id: str) -> list[AnimationJobRead]:
        return self.repository.list_for_series(series_id)

    def list_for_direction(self, direction_job_id: str) -> list[AnimationJobRead]:
        return self.repository.list_for_direction(direction_job_id)

    def queue(self, job_id: str) -> AnimationJobRead:
        job = self.get(job_id)
        if job.status not in {
            AnimationJobStatus.PLANNED,
            AnimationJobStatus.FAILED,
        }:
            raise ConflictError("Only planned or failed animation jobs can be queued")

        keyframe = self.visual_repository.get(job.keyframe_asset_id)
        if keyframe is None:
            raise NotFoundError("Animation keyframe asset not found")
        if keyframe.status != VisualAssetStatus.SUCCEEDED:
            raise ConflictError("Animation keyframe must finish successfully before animation")
        if keyframe.review_status != VisualAssetReviewStatus.APPROVED:
            raise ConflictError("Approve the shot keyframe before animation")
        if not keyframe.images or not keyframe.images[0].storage_path:
            raise ConflictError("Animation keyframe is not stored permanently")
        if not Path(keyframe.images[0].storage_path).is_file():
            raise ConflictError("Stored animation keyframe file is missing")

        queued = self.repository.mark_queued(job_id)
        if queued is None:
            raise NotFoundError("Animation job not found")
        return queued

    def fail(self, job_id: str, error: str) -> AnimationJobRead:
        failed = self.repository.fail(job_id, error)
        if failed is None:
            raise NotFoundError("Animation job not found")
        return failed

    def review(self, job_id: str, request: AnimationReviewRequest) -> AnimationJobRead:
        job = self.get(job_id)
        if job.status != AnimationJobStatus.SUCCEEDED:
            raise ConflictError("Only completed animated shots can be reviewed")
        reviewed = self.repository.review(job_id, request)
        if reviewed is None:
            raise NotFoundError("Animation job not found")
        return reviewed
