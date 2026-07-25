import shutil

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import (
    get_direction_job_service,
    get_finalization_job_service,
    get_lip_sync_job_service,
    get_sound_mix_job_service,
)
from app.tasks.finalization import render_finalization_job
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import DirectionJobStatus, DirectionReviewStatus
from packages.direction.service import DirectionJobService
from packages.finalization.models import (
    FinalizationJobRead,
    FinalizationPlanRequest,
    FinalizationReviewRequest,
)
from packages.finalization.planner import FinalizationPlanner
from packages.finalization.service import FinalizationJobService
from packages.lipsync.service import LipSyncJobService
from packages.sound.service import SoundMixJobService

router = APIRouter()


@router.get("/finalization/health")
def finalization_health() -> dict[str, object]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    available = bool(ffmpeg and ffprobe)
    return {
        "available": available,
        "ffmpeg_available": bool(ffmpeg),
        "ffprobe_available": bool(ffprobe),
        "detail": (
            "FFmpeg and FFprobe are ready"
            if available
            else "Install FFmpeg and FFprobe"
        ),
    }


@router.post(
    "/direction-jobs/{direction_job_id}/finalization-jobs/plan",
    response_model=FinalizationJobRead,
    status_code=status.HTTP_201_CREATED,
)
def plan_finalization(
    direction_job_id: str,
    request: FinalizationPlanRequest,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    sound_service: SoundMixJobService = Depends(get_sound_mix_job_service),
    lip_sync_service: LipSyncJobService = Depends(get_lip_sync_job_service),
    finalization_service: FinalizationJobService = Depends(
        get_finalization_job_service
    ),
) -> FinalizationJobRead:
    try:
        direction = direction_service.get(direction_job_id)
        if direction.status != DirectionJobStatus.SUCCEEDED or direction.result is None:
            raise ConflictError(
                "Direction must finish successfully before finalization"
            )
        if direction.review_status != DirectionReviewStatus.APPROVED:
            raise ConflictError("Approve the direction before finalization")
        spec = FinalizationPlanner().plan(
            direction_job_id,
            direction.result,
            sound_service.list_for_direction(direction_job_id),
            lip_sync_service.list_for_series(direction.series_id),
            request,
        )
        job = finalization_service.create(direction.series_id, spec)
        queued = finalization_service.queue(job.id)
        try:
            render_finalization_job.delay(queued.id)
        except Exception as exc:
            finalization_service.fail(
                queued.id,
                f"Could not queue finalization: {exc}",
            )
        return finalization_service.get(queued.id)
    except (ConflictError, NotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/series/{series_id}/finalization-jobs",
    response_model=list[FinalizationJobRead],
)
def list_finalization_jobs(
    series_id: str,
    service: FinalizationJobService = Depends(get_finalization_job_service),
) -> list[FinalizationJobRead]:
    return service.list_for_series(series_id)


@router.get("/finalization-jobs/{job_id}", response_model=FinalizationJobRead)
def get_finalization_job(
    job_id: str,
    service: FinalizationJobService = Depends(get_finalization_job_service),
) -> FinalizationJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/finalization-jobs/{job_id}/retry", response_model=FinalizationJobRead)
def retry_finalization_job(
    job_id: str,
    service: FinalizationJobService = Depends(get_finalization_job_service),
) -> FinalizationJobRead:
    try:
        queued = service.queue(job_id)
        try:
            render_finalization_job.delay(queued.id)
        except Exception as exc:
            return service.fail(
                queued.id,
                f"Could not queue finalization: {exc}",
            )
        return service.get(job_id)
    except (ConflictError, NotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post("/finalization-jobs/{job_id}/review", response_model=FinalizationJobRead)
def review_finalization_job(
    job_id: str,
    request: FinalizationReviewRequest,
    service: FinalizationJobService = Depends(get_finalization_job_service),
) -> FinalizationJobRead:
    try:
        return service.review(job_id, request)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
