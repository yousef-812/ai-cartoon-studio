from typing import Protocol

from packages.images.models import ImageProviderResult
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewRequest,
    VisualAssetSpec,
)


class VisualAssetRepository(Protocol):
    def create_many(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[VisualAssetSpec],
        provider: str,
    ) -> list[VisualAssetRead]: ...

    def get(self, asset_id: str) -> VisualAssetRead | None: ...

    def get_by_key(
        self, direction_job_id: str, key: str
    ) -> VisualAssetRead | None: ...

    def list_for_series(self, series_id: str) -> list[VisualAssetRead]: ...

    def mark_queued(self, asset_id: str) -> VisualAssetRead | None: ...

    def mark_running(
        self, asset_id: str, provider_job_id: str | None = None
    ) -> VisualAssetRead | None: ...

    def set_provider_job(
        self, asset_id: str, provider_job_id: str
    ) -> VisualAssetRead | None: ...

    def complete(
        self, asset_id: str, result: ImageProviderResult
    ) -> VisualAssetRead | None: ...

    def fail(self, asset_id: str, error: str) -> VisualAssetRead | None: ...

    def review(
        self, asset_id: str, request: VisualAssetReviewRequest
    ) -> VisualAssetRead | None: ...
