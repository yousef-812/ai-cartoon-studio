import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_animation_job_service,
    get_direction_job_service,
    get_lip_sync_job_service,
    get_lip_sync_provider,
    get_series_service,
    get_voice_job_service,
)
from app.tasks.lipsync import generate_lip_sync_job
from packages.animations.service import AnimationJobService
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import DirectionJobStatus, DirectionReviewStatus
from packages.direction.service import DirectionJobService
from packages.lipsync.http_provider import SelfHostedLipSyncProvider
from packages.lipsync.models import (
    LipSyncJobRead,
    LipSyncPlanRequest,
    LipSyncProviderHealth,
    LipSyncReviewRequest,
)
from packages.lipsync.planner import LipSyncPlanner
from packages.lipsync.service import LipSyncJobService
from packages.series.service import SeriesService
from packages.voices.service import VoiceJobService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _enqueue(job: LipSyncJobRead, service: LipSyncJobService) -> LipSyncJobRead:
    try:
        generate_lip_sync_job.delay(job.id)
        return job
    except Exception as error:
        return service.fail(job.id, f"Could not enqueue lip-sync worker: {error}")


@router.get("/lip-sync/health", response_model=LipSyncProviderHealth)
def lip_sync_health(
    provider: SelfHostedLipSyncProvider = Depends(get_lip_sync_provider),
) -> LipSyncProviderHealth:
    return asyncio.run(provider.health())


@router.post(
    "/direction-jobs/{direction_job_id}/lip-sync-jobs/plan",
    response_model=list[LipSyncJobRead],
    status_code=status.HTTP_201_CREATED,
)
def create_lip_sync_plan(
    direction_job_id: str,
    payload: LipSyncPlanRequest,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    animation_service: AnimationJobService = Depends(get_animation_job_service),
    voice_service: VoiceJobService = Depends(get_voice_job_service),
    lip_sync_service: LipSyncJobService = Depends(get_lip_sync_job_service),
) -> list[LipSyncJobRead]:
    try:
        direction_job = direction_service.get(direction_job_id)
        if direction_job.status != DirectionJobStatus.SUCCEEDED or direction_job.result is None:
            raise ConflictError("Direction must finish successfully before lip-sync planning")
        if direction_job.review_status != DirectionReviewStatus.APPROVED:
            raise ConflictError("Approve direction before lip-sync planning")

        animations = animation_service.list_for_direction(direction_job.id)
        voices = voice_service.list_for_script(direction_job.script_job_id)
        specs = LipSyncPlanner().plan(direction_job.result, animations, voices, payload)
        jobs = lip_sync_service.create_plan(
            direction_job.series_id,
            direction_job.id,
            specs,
            provider=settings.lip_sync_provider,
        )
        queued: list[LipSyncJobRead] = []
        for job in jobs:
            if job.status.value in {"planned", "failed"}:
                queued.append(_enqueue(lip_sync_service.queue(job.id), lip_sync_service))
            else:
                queued.append(job)
        return queued
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get("/series/{series_id}/lip-sync-jobs", response_model=list[LipSyncJobRead])
def list_lip_sync_jobs(
    series_id: str,
    service: LipSyncJobService = Depends(get_lip_sync_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[LipSyncJobRead]:
    try:
        series_service.get(series_id)
        return service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/lip-sync-jobs/{job_id}", response_model=LipSyncJobRead)
def get_lip_sync_job(
    job_id: str,
    service: LipSyncJobService = Depends(get_lip_sync_job_service),
) -> LipSyncJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/lip-sync-jobs/{job_id}/retry",
    response_model=LipSyncJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_lip_sync_job(
    job_id: str,
    service: LipSyncJobService = Depends(get_lip_sync_job_service),
) -> LipSyncJobRead:
    try:
        return _enqueue(service.queue(job_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/lip-sync-jobs/{job_id}/review", response_model=LipSyncJobRead)
def review_lip_sync_job(
    job_id: str,
    payload: LipSyncReviewRequest,
    service: LipSyncJobService = Depends(get_lip_sync_job_service),
) -> LipSyncJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
