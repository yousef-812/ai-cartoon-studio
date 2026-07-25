import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_animation_job_service,
    get_direction_job_service,
    get_lip_sync_job_service,
    get_series_service,
    get_sound_mix_job_service,
    get_sound_provider,
)
from app.tasks.sound import generate_sound_mix_job
from packages.animations.service import AnimationJobService
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import DirectionJobStatus, DirectionReviewStatus
from packages.direction.service import DirectionJobService
from packages.lipsync.service import LipSyncJobService
from packages.mixing.ffmpeg import FFmpegSoundMixer
from packages.series.service import SeriesService
from packages.sound.http_provider import SelfHostedSoundProvider
from packages.sound.models import (
    SoundMixJobRead,
    SoundMixReviewRequest,
    SoundPlanRequest,
    SoundSystemHealth,
)
from packages.sound.planner import SoundDesignPlanner
from packages.sound.service import SoundMixJobService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _enqueue(job: SoundMixJobRead, service: SoundMixJobService) -> SoundMixJobRead:
    try:
        generate_sound_mix_job.delay(job.id)
        return job
    except Exception as error:
        return service.fail(job.id, f"Could not enqueue sound worker: {error}")


@router.get("/sound/health", response_model=SoundSystemHealth)
def sound_health(
    provider: SelfHostedSoundProvider = Depends(get_sound_provider),
) -> SoundSystemHealth:
    provider_health = asyncio.run(provider.health())
    ffmpeg_available = FFmpegSoundMixer(settings.ffmpeg_binary).available()
    detail_parts = [provider_health.detail]
    if not ffmpeg_available:
        detail_parts.append("FFmpeg is not available on the API/worker host.")
    return SoundSystemHealth(
        available=provider_health.available and ffmpeg_available,
        provider=provider_health,
        ffmpeg_available=ffmpeg_available,
        detail=" ".join(part for part in detail_parts if part),
    )


@router.post(
    "/direction-jobs/{direction_job_id}/sound-jobs/plan",
    response_model=list[SoundMixJobRead],
    status_code=status.HTTP_201_CREATED,
)
def create_sound_plan(
    direction_job_id: str,
    payload: SoundPlanRequest,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    animation_service: AnimationJobService = Depends(get_animation_job_service),
    lip_sync_service: LipSyncJobService = Depends(get_lip_sync_job_service),
    sound_service: SoundMixJobService = Depends(get_sound_mix_job_service),
) -> list[SoundMixJobRead]:
    try:
        direction_job = direction_service.get(direction_job_id)
        if direction_job.status != DirectionJobStatus.SUCCEEDED or direction_job.result is None:
            raise ConflictError("Direction must finish successfully before sound design")
        if direction_job.review_status != DirectionReviewStatus.APPROVED:
            raise ConflictError("Approve direction before sound design")
        animations = animation_service.list_for_direction(direction_job_id)
        lip_sync_jobs = lip_sync_service.list_for_direction(direction_job_id)
        specs = SoundDesignPlanner().plan(
            direction_job.result,
            animations,
            lip_sync_jobs,
            payload,
        )
        jobs = sound_service.create_plan(
            direction_job.series_id,
            direction_job.id,
            specs,
            provider=settings.sound_provider,
        )
        queued: list[SoundMixJobRead] = []
        for job in jobs:
            if job.status.value in {"planned", "failed"}:
                queued.append(_enqueue(sound_service.queue(job.id), sound_service))
            else:
                queued.append(job)
        return queued
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get("/series/{series_id}/sound-jobs", response_model=list[SoundMixJobRead])
def list_sound_jobs(
    series_id: str,
    service: SoundMixJobService = Depends(get_sound_mix_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[SoundMixJobRead]:
    try:
        series_service.get(series_id)
        return service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/sound-jobs/{job_id}", response_model=SoundMixJobRead)
def get_sound_job(
    job_id: str,
    service: SoundMixJobService = Depends(get_sound_mix_job_service),
) -> SoundMixJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/sound-jobs/{job_id}/retry",
    response_model=SoundMixJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_sound_job(
    job_id: str,
    service: SoundMixJobService = Depends(get_sound_mix_job_service),
) -> SoundMixJobRead:
    try:
        return _enqueue(service.queue(job_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/sound-jobs/{job_id}/review", response_model=SoundMixJobRead)
def review_sound_job(
    job_id: str,
    payload: SoundMixReviewRequest,
    service: SoundMixJobService = Depends(get_sound_mix_job_service),
) -> SoundMixJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
