import asyncio

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.dependencies import (
    get_audio_provider,
    get_character_service,
    get_script_job_service,
    get_series_service,
    get_voice_job_service,
)
from app.tasks.voice import generate_voice_job
from packages.audio.models import AudioProviderHealth
from packages.audio.openai_compatible import OpenAICompatibleAudioProvider
from packages.characters.service import CharacterService
from packages.common.errors import ConflictError, NotFoundError
from packages.scripts.models import ScriptJobStatus, ScriptReviewStatus
from packages.scripts.service import ScriptJobService
from packages.series.service import SeriesService
from packages.voices.models import VoiceJobRead, VoicePlanRequest, VoiceReviewRequest
from packages.voices.planner import VoicePlanner
from packages.voices.service import VoiceJobService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


def _enqueue(job: VoiceJobRead, service: VoiceJobService) -> VoiceJobRead:
    try:
        generate_voice_job.delay(job.id)
        return job
    except Exception as error:
        return service.fail(job.id, f"Could not enqueue voice worker: {error}")


@router.get("/voice/health", response_model=AudioProviderHealth)
def voice_health(
    provider: OpenAICompatibleAudioProvider = Depends(get_audio_provider),
) -> AudioProviderHealth:
    return asyncio.run(provider.health())


@router.post(
    "/script-jobs/{script_job_id}/voice-jobs/plan",
    response_model=list[VoiceJobRead],
    status_code=status.HTTP_201_CREATED,
)
def create_voice_plan(
    script_job_id: str,
    payload: VoicePlanRequest,
    script_service: ScriptJobService = Depends(get_script_job_service),
    character_service: CharacterService = Depends(get_character_service),
    voice_service: VoiceJobService = Depends(get_voice_job_service),
) -> list[VoiceJobRead]:
    try:
        script_job = script_service.get(script_job_id)
        if script_job.status != ScriptJobStatus.SUCCEEDED or script_job.result is None:
            raise ConflictError("Screenplay must finish successfully before voice planning")
        if script_job.review_status != ScriptReviewStatus.APPROVED:
            raise ConflictError("Approve the screenplay before voice planning")
        characters = character_service.list_for_series(script_job.series_id)
        specs = VoicePlanner().plan(script_job.result, characters, payload)
        jobs = voice_service.create_plan(
            script_job.series_id,
            script_job.id,
            specs,
            provider=settings.voice_provider,
        )
        queued: list[VoiceJobRead] = []
        for job in jobs:
            if job.status.value in {"planned", "failed"}:
                queued.append(_enqueue(voice_service.queue(job.id), voice_service))
            else:
                queued.append(job)
        return queued
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get("/series/{series_id}/voice-jobs", response_model=list[VoiceJobRead])
def list_voice_jobs(
    series_id: str,
    service: VoiceJobService = Depends(get_voice_job_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[VoiceJobRead]:
    try:
        series_service.get(series_id)
        return service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/voice-jobs/{job_id}", response_model=VoiceJobRead)
def get_voice_job(
    job_id: str,
    service: VoiceJobService = Depends(get_voice_job_service),
) -> VoiceJobRead:
    try:
        return service.get(job_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/voice-jobs/{job_id}/retry",
    response_model=VoiceJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_voice_job(
    job_id: str,
    service: VoiceJobService = Depends(get_voice_job_service),
) -> VoiceJobRead:
    try:
        return _enqueue(service.queue(job_id), service)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.post("/voice-jobs/{job_id}/review", response_model=VoiceJobRead)
def review_voice_job(
    job_id: str,
    payload: VoiceReviewRequest,
    service: VoiceJobService = Depends(get_voice_job_service),
) -> VoiceJobRead:
    try:
        return service.review(job_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
