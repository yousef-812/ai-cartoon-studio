from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import get_series_service, get_story_job_service
from app.tasks.story import generate_story_job
from packages.common.errors import ConflictError, NotFoundError
from packages.series.service import SeriesService
from packages.stories.models import (
    StoryGenerationJobRead,
    StoryGenerationRequest,
    StoryReviewRequest,
)
from packages.stories.service import StoryJobService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/series/{series_id}/story-jobs",
    response_model=StoryGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_story_job(
    series_id: str,
    payload: StoryGenerationRequest,
    story_service: StoryJobService = Depends(get_story_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> StoryGenerationJobRead:
    try:
        series_service.get(series_id)
        job = story_service.create(
            series_id,
            payload,
            provider=settings.llm_provider,
            model=settings.llm_model,
        )
        try:
            generate_story_job.delay(job.id)
            return job
        except Exception as error:
            return story_service.fail(job.id, f"Could not enqueue story worker: {error}")
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get(
    "/series/{series_id}/story-jobs",
    response_model=list[StoryGenerationJobRead],
)
def list_story_jobs(
    series_id: str,
    story_service: StoryJobService = Depends(get_story_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[StoryGenerationJobRead]:
    try:
        series_service.get(series_id)
        return story_service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/story-jobs/{job_id}", response_model=StoryGenerationJobRead)
def get_story_job(
    job_id: str,
    service: StoryJobService = Depends(get_story_job_service),
) -> StoryGenerationJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/story-jobs/{job_id}/retry",
    response_model=StoryGenerationJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_story_job(
    job_id: str,
    service: StoryJobService = Depends(get_story_job_service),
) -> StoryGenerationJobRead:
    try:
        job = service.retry(job_id)
        try:
            generate_story_job.delay(job.id)
            return job
        except Exception as error:
            return service.fail(job.id, f"Could not enqueue story worker: {error}")
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/story-jobs/{job_id}/review", response_model=StoryGenerationJobRead)
def review_story_job(
    job_id: str,
    payload: StoryReviewRequest,
    service: StoryJobService = Depends(get_story_job_service),
) -> StoryGenerationJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
