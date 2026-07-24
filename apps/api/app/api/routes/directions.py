from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_direction_job_service,
    get_script_job_service,
    get_series_service,
)
from app.tasks.direction import generate_direction_job
from packages.common.errors import ConflictError, NotFoundError
from packages.direction.models import (
    DirectionGenerationJobRead,
    DirectionGenerationRequest,
    DirectionReviewRequest,
)
from packages.direction.service import DirectionJobService
from packages.scripts.models import ScriptJobStatus, ScriptReviewStatus
from packages.scripts.service import ScriptJobService
from packages.series.service import SeriesService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/script-jobs/{script_job_id}/direction-jobs",
    response_model=DirectionGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_direction_job(
    script_job_id: str,
    payload: DirectionGenerationRequest,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    script_service: ScriptJobService = Depends(get_script_job_service),
) -> DirectionGenerationJobRead:
    try:
        script_job = script_service.get(script_job_id)
        if script_job.status != ScriptJobStatus.SUCCEEDED or script_job.result is None:
            raise ConflictError("The screenplay must finish successfully before directing")
        if script_job.review_status != ScriptReviewStatus.APPROVED:
            raise ConflictError("Approve the screenplay before directing")

        job = direction_service.create(
            script_job.series_id,
            script_job.id,
            payload,
            provider=settings.llm_provider,
            model=settings.llm_model,
        )
        try:
            generate_direction_job.delay(job.id)
            return job
        except Exception as error:
            return direction_service.fail(job.id, f"Could not enqueue direction worker: {error}")
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get(
    "/series/{series_id}/direction-jobs",
    response_model=list[DirectionGenerationJobRead],
)
def list_direction_jobs(
    series_id: str,
    direction_service: DirectionJobService = Depends(get_direction_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[DirectionGenerationJobRead]:
    try:
        series_service.get(series_id)
        return direction_service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/direction-jobs/{job_id}", response_model=DirectionGenerationJobRead)
def get_direction_job(
    job_id: str,
    service: DirectionJobService = Depends(get_direction_job_service),
) -> DirectionGenerationJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/direction-jobs/{job_id}/retry",
    response_model=DirectionGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_direction_job(
    job_id: str,
    service: DirectionJobService = Depends(get_direction_job_service),
) -> DirectionGenerationJobRead:
    try:
        job = service.retry(job_id)
        try:
            generate_direction_job.delay(job.id)
            return job
        except Exception as error:
            return service.fail(job.id, f"Could not enqueue direction worker: {error}")
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/direction-jobs/{job_id}/review", response_model=DirectionGenerationJobRead)
def review_direction_job(
    job_id: str,
    payload: DirectionReviewRequest,
    service: DirectionJobService = Depends(get_direction_job_service),
) -> DirectionGenerationJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
