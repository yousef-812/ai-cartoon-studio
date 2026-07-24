from packages.common.errors import ConflictError, NotFoundError
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewRequest,
    VisualAssetReviewStatus,
    VisualAssetSpec,
    VisualAssetStatus,
)
from packages.visuals.repository import VisualAssetRepository


class VisualAssetService:
    def __init__(self, repository: VisualAssetRepository) -> None:
        self.repository = repository

    def create_plan(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[VisualAssetSpec],
        provider: str,
    ) -> list[VisualAssetRead]:
        return self.repository.create_many(series_id, direction_job_id, specs, provider)

    def get(self, asset_id: str) -> VisualAssetRead:
        asset = self.repository.get(asset_id)
        if asset is None:
            raise NotFoundError("Visual asset not found")
        return asset

    def list_for_series(self, series_id: str) -> list[VisualAssetRead]:
        return self.repository.list_for_series(series_id)

    def queue(self, asset_id: str) -> VisualAssetRead:
        asset = self.get(asset_id)
        if asset.status not in {
            VisualAssetStatus.PLANNED,
            VisualAssetStatus.BLOCKED,
            VisualAssetStatus.FAILED,
        }:
            raise ConflictError("Only planned, blocked, or failed assets can be queued")

        missing: list[str] = []
        for key in asset.spec.dependency_keys:
            dependency = self.repository.get_by_key(asset.direction_job_id, key)
            if dependency is None or dependency.review_status != VisualAssetReviewStatus.APPROVED:
                missing.append(key)
        if missing:
            raise ConflictError(
                "Approve required visual references first: " + ", ".join(missing)
            )

        queued = self.repository.mark_queued(asset_id)
        if queued is None:
            raise NotFoundError("Visual asset not found")
        return queued

    def fail(self, asset_id: str, error: str) -> VisualAssetRead:
        failed = self.repository.fail(asset_id, error)
        if failed is None:
            raise NotFoundError("Visual asset not found")
        return failed

    def review(self, asset_id: str, request: VisualAssetReviewRequest) -> VisualAssetRead:
        asset = self.get(asset_id)
        if asset.status != VisualAssetStatus.SUCCEEDED:
            raise ConflictError("Only completed visual assets can be reviewed")
        reviewed = self.repository.review(asset_id, request)
        if reviewed is None:
            raise NotFoundError("Visual asset not found")
        return reviewed
