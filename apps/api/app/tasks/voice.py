import asyncio

from celery import Task

from app.audio_provider import build_audio_provider
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.voices import SQLVoiceJobRepository
from app.worker import celery_app
from packages.artifacts.local_store import LocalArtifactStore
from packages.audio.errors import AudioProviderError, AudioProviderUnavailableError
from packages.common.errors import NotFoundError


@celery_app.task(bind=True, max_retries=2, name="voices.generate")
def generate_voice_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    repository = SQLVoiceJobRepository(session)
    try:
        job = repository.get(job_id)
        if job is None:
            raise NotFoundError("Voice job not found")
        repository.mark_running(job_id)

        provider = build_audio_provider()
        synthesized = asyncio.run(provider.synthesize(job.spec.synthesis))
        store = LocalArtifactStore(settings.storage_path)
        audio = store.persist_audio(
            synthesized,
            series_id=job.series_id,
            voice_job_id=job.id,
        )
        completed = repository.complete(job_id, audio)
        return completed.model_dump(mode="json") if completed else audio.model_dump(mode="json")
    except AudioProviderUnavailableError as error:
        if self.request.retries < self.max_retries:
            repository.mark_queued(job_id)
            raise self.retry(exc=error, countdown=min(30 * (2**self.request.retries), 180))
        repository.fail(job_id, str(error))
        raise
    except (AudioProviderError, NotFoundError, ValueError) as error:
        repository.fail(job_id, str(error))
        raise
    except Exception as error:
        repository.fail(job_id, f"Unexpected voice generation error: {error}")
        raise
    finally:
        session.close()
