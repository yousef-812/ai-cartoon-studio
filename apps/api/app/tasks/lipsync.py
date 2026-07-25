import asyncio

from celery import Task

from app.core.config import settings
from app.db.session import SessionLocal
from app.lip_sync_provider import build_lip_sync_provider
from app.repositories.lipsync import SQLLipSyncJobRepository
from app.worker import celery_app
from packages.common.errors import NotFoundError
from packages.lipsync.errors import (
    LipSyncProviderError,
    LipSyncProviderUnavailableError,
)
from packages.lipsync.storage import persist_lip_sync_video
from packages.videos.models import VideoProviderResult


@celery_app.task(bind=True, max_retries=2, name="lip_sync.generate")
def generate_lip_sync_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    repository = SQLLipSyncJobRepository(session)
    try:
        job = repository.get(job_id)
        if job is None:
            raise NotFoundError("Lip-sync job not found")
        repository.mark_running(job_id)

        provider = build_lip_sync_provider()
        rendered = asyncio.run(provider.synthesize(job.spec.generation))
        video = persist_lip_sync_video(
            settings.storage_path,
            rendered,
            series_id=job.series_id,
            job_id=job.id,
        )
        result = VideoProviderResult(completed=True, videos=[video])
        completed = repository.complete(job_id, result)
        return completed.model_dump(mode="json") if completed else result.model_dump(mode="json")
    except LipSyncProviderUnavailableError as error:
        if self.request.retries < self.max_retries:
            repository.mark_queued(job_id)
            raise self.retry(exc=error, countdown=min(30 * (2**self.request.retries), 180))
        repository.fail(job_id, str(error))
        raise
    except (LipSyncProviderError, NotFoundError, ValueError) as error:
        repository.fail(job_id, str(error))
        raise
    except Exception as error:
        repository.fail(job_id, f"Unexpected lip-sync generation error: {error}")
        raise
    finally:
        session.close()
