from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import get_script_job_service, get_series_service, get_story_job_service
from app.tasks.script import generate_script_job
from packages.common.errors import ConflictError, NotFoundError
from packages.scripts.models import (
    ScriptGenerationJobRead,
    ScriptGenerationRequest,
    ScriptReviewRequest,
)
from packages.scripts.service import ScriptJobService
from packages.series.service import SeriesService
from packages.stories.models import StoryJobStatus, StoryReviewStatus
from packages.stories.service import StoryJobService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/story-jobs/{story_job_id}/script-jobs",
    response_model=ScriptGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_script_job(
    story_job_id: str,
    payload: ScriptGenerationRequest,
    script_service: ScriptJobService = Depends(get_script_job_service),
    story_service: StoryJobService = Depends(get_story_job_service),
) -> ScriptGenerationJobRead:
    try:
        story_job = story_service.get(story_job_id)
        if story_job.status is not StoryJobStatus.SUCCEEDED or story_job.result is None:
            raise ConflictError("The story must finish successfully before screenplay generation")
        if story_job.review_status is not StoryReviewStatus.APPROVED:
            raise ConflictError("Approve the story before screenplay generation")

        resolved_payload = payload
        if payload.target_duration_seconds is None:
            resolved_payload = payload.model_copy(
                update={"target_duration_seconds": story_job.request.target_duration_seconds}
            )
        job = script_service.create(
            story_job.series_id,
            story_job.id,
            resolved_payload,
            provider=settings.llm_provider,
            model=settings.llm_model,
        )
        try:
            generate_script_job.delay(job.id)
            return job
        except Exception as error:
            return script_service.fail(job.id, f"Could not enqueue script worker: {error}")
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get(
    "/series/{series_id}/script-jobs",
    response_model=list[ScriptGenerationJobRead],
)
def list_script_jobs(
    series_id: str,
    script_service: ScriptJobService = Depends(get_script_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[ScriptGenerationJobRead]:
    try:
        series_service.get(series_id)
        return script_service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/script-jobs/{job_id}", response_model=ScriptGenerationJobRead)
def get_script_job(
    job_id: str,
    service: ScriptJobService = Depends(get_script_job_service),
) -> ScriptGenerationJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/script-jobs/{job_id}/retry",
    response_model=ScriptGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_script_job(
    job_id: str,
    service: ScriptJobService = Depends(get_script_job_service),
) -> ScriptGenerationJobRead:
    try:
        job = service.retry(job_id)
        try:
            generate_script_job.delay(job.id)
            return job
        except Exception as error:
            return service.fail(job.id, f"Could not enqueue script worker: {error}")
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/script-jobs/{job_id}/review", response_model=ScriptGenerationJobRead)
def review_script_job(
    job_id: str,
    payload: ScriptReviewRequest,
    service: ScriptJobService = Depends(get_script_job_service),
) -> ScriptGenerationJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
