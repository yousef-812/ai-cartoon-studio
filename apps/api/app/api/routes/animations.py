import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_animation_job_service,
    get_direction_job_service,
    get_series_service,
    get_video_provider,
    get_visual_asset_service,
)
from app.tasks.animation import generate_animation_job
from packages.animations.models import (
    AnimationJobRead,
    AnimationPlanRequest,
    AnimationReviewRequest,
)
from packages.animations.planner import AnimationPlanner
from packages.animations.service import AnimationJobService
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import DirectionJobStatus, DirectionReviewStatus
from packages.direction.service import DirectionJobService
from packages.series.service import SeriesService
from packages.videos.comfyui import ComfyUIVideoProvider
from packages.videos.models import VideoProviderHealth
from packages.visuals.service import VisualAssetService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _enqueue(job: AnimationJobRead, service: AnimationJobService) -> AnimationJobRead:
    try:
        generate_animation_job.delay(job.id)
        return job
    except Exception as error:
        return service.fail(job.id, f"Could not enqueue animation worker: {error}")


@router.get("/video/health", response_model=VideoProviderHealth)
def video_health(
    provider: ComfyUIVideoProvider = Depends(get_video_provider),
) -> VideoProviderHealth:
    return asyncio.run(provider.health())


@router.post(
    "/direction-jobs/{direction_job_id}/animation-jobs/plan",
    response_model=list[AnimationJobRead],
    status_code=status.HTTP_201_CREATED,
)
def create_animation_plan(
    direction_job_id: str,
    payload: AnimationPlanRequest,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    visual_service: VisualAssetService = Depends(get_visual_asset_service),
    animation_service: AnimationJobService = Depends(get_animation_job_service),
) -> list[AnimationJobRead]:
    try:
        direction_job = direction_service.get(direction_job_id)
        if direction_job.status != DirectionJobStatus.SUCCEEDED or direction_job.result is None:
            raise ConflictError("Direction must finish successfully before animation planning")
        if direction_job.review_status != DirectionReviewStatus.APPROVED:
            raise ConflictError("Approve direction before animation planning")

        visual_assets = visual_service.list_for_direction(direction_job.id)
        specs = AnimationPlanner().plan(direction_job.result, visual_assets, payload)
        jobs = animation_service.create_plan(
            direction_job.series_id,
            direction_job.id,
            specs,
            provider=settings.video_provider,
        )
        return [_enqueue(animation_service.queue(job.id), animation_service) for job in jobs]
    except (ConflictError, NotFoundError, KeyError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get(
    "/series/{series_id}/animation-jobs",
    response_model=list[AnimationJobRead],
)
def list_animation_jobs(
    series_id: str,
    service: AnimationJobService = Depends(get_animation_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[AnimationJobRead]:
    try:
        series_service.get(series_id)
        return service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/animation-jobs/{job_id}", response_model=AnimationJobRead)
def get_animation_job(
    job_id: str,
    service: AnimationJobService = Depends(get_animation_job_service),
) -> AnimationJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/animation-jobs/{job_id}/retry",
    response_model=AnimationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_animation_job(
    job_id: str,
    service: AnimationJobService = Depends(get_animation_job_service),
) -> AnimationJobRead:
    try:
        return _enqueue(service.queue(job_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/animation-jobs/{job_id}/review", response_model=AnimationJobRead)
def review_animation_job(
    job_id: str,
    payload: AnimationReviewRequest,
    service: AnimationJobService = Depends(get_animation_job_service),
) -> AnimationJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
