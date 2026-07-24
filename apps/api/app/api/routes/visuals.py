from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_character_service,
    get_direction_job_service,
    get_series_service,
    get_visual_asset_service,
)
from app.tasks.visual import generate_visual_asset
from packages.characters.service import CharacterService
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import DirectionJobStatus, DirectionReviewStatus
from packages.direction.service import DirectionJobService
from packages.series.service import SeriesService
from packages.visuals.models import VisualAssetRead, VisualAssetReviewRequest
from packages.visuals.planner import VisualAssetPlanner
from packages.visuals.service import VisualAssetService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _enqueue(asset: VisualAssetRead, service: VisualAssetService) -> VisualAssetRead:
    try:
        generate_visual_asset.delay(asset.id)
        return asset
    except Exception as error:
        return service.fail(asset.id, f"Could not enqueue visual worker: {error}")


@router.post(
    "/direction-jobs/{direction_job_id}/visual-assets/plan",
    response_model=list[VisualAssetRead],
    status_code=status.HTTP_201_CREATED,
)
def create_visual_plan(
    direction_job_id: str,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    series_service: SeriesService = Depends(get_series_service),
    character_service: CharacterService = Depends(get_character_service),
    asset_service: VisualAssetService = Depends(get_visual_asset_service),
) -> list[VisualAssetRead]:
    try:
        direction_job = direction_service.get(direction_job_id)
        if direction_job.status != DirectionJobStatus.SUCCEEDED or direction_job.result is None:
            raise ConflictError("Direction must finish successfully before visual planning")
        if direction_job.review_status != DirectionReviewStatus.APPROVED:
            raise ConflictError("Approve direction before visual planning")

        series = series_service.get(direction_job.series_id)
        characters = character_service.list_for_series(direction_job.series_id)
        locations = series_service.list_locations(direction_job.series_id)
        specs = VisualAssetPlanner().plan(series, characters, locations, direction_job.result)
        assets = asset_service.create_plan(
            direction_job.series_id,
            direction_job.id,
            specs,
            provider=settings.image_provider,
        )

        results: list[VisualAssetRead] = []
        for asset in assets:
            if asset.spec.dependency_keys:
                results.append(asset)
                continue
            queued = asset_service.queue(asset.id)
            results.append(_enqueue(queued, asset_service))
        return results
    except (ConflictError, NotFoundError, KeyError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get(
    "/series/{series_id}/visual-assets",
    response_model=list[VisualAssetRead],
)
def list_visual_assets(
    series_id: str,
    asset_service: VisualAssetService = Depends(get_visual_asset_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[VisualAssetRead]:
    try:
        series_service.get(series_id)
        return asset_service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/visual-assets/{asset_id}", response_model=VisualAssetRead)
def get_visual_asset(
    asset_id: str,
    service: VisualAssetService = Depends(get_visual_asset_service),
) -> VisualAssetRead:
    try:
        return service.get(asset_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/visual-assets/{asset_id}/queue",
    response_model=VisualAssetRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def queue_visual_asset(
    asset_id: str,
    service: VisualAssetService = Depends(get_visual_asset_service),
) -> VisualAssetRead:
    try:
        return _enqueue(service.queue(asset_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/visual-assets/{asset_id}/retry",
    response_model=VisualAssetRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_visual_asset(
    asset_id: str,
    service: VisualAssetService = Depends(get_visual_asset_service),
) -> VisualAssetRead:
    try:
        return _enqueue(service.queue(asset_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/visual-assets/{asset_id}/review", response_model=VisualAssetRead)
def review_visual_asset(
    asset_id: str,
    payload: VisualAssetReviewRequest,
    service: VisualAssetService = Depends(get_visual_asset_service),
) -> VisualAssetRead:
    try:
        return service.review(asset_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
