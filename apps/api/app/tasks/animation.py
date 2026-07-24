import asyncio

from celery import Task

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.animations import SQLAnimationJobRepository
from app.video_provider import build_video_provider
from app.worker import celery_app
from packages.artifacts.local_store import LocalArtifactStore
from packages.common.errors import NotFoundError
from packages.videos.errors import (
    VideoProviderError,
    VideoProviderUnavailableError,
)


@celery_app.task(bind=True, max_retries=2, name="animations.generate")
def generate_animation_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    repository = SQLAnimationJobRepository(session)
    try:
        job = repository.get(job_id)
        if job is None:
            raise NotFoundError("Animation job not found")
        repository.mark_running(job_id)

        provider = build_video_provider()
        submission = asyncio.run(provider.submit(job.spec.generation))
        repository.set_provider_job(job_id, submission.provider_job_id)
        result = asyncio.run(provider.wait_for_result(submission.provider_job_id))
        store = LocalArtifactStore(
            settings.storage_path,
            allowed_base_url=settings.video_base_url,
            timeout_seconds=settings.video_timeout_seconds,
        )
        persisted = asyncio.run(
            store.persist_video_result(
                result,
                series_id=job.series_id,
                animation_id=job.id,
            )
        )
        completed = repository.complete(job_id, persisted)
        return completed.model_dump(mode="json") if completed else persisted.model_dump(mode="json")
    except VideoProviderUnavailableError as error:
        if self.request.retries < self.max_retries:
            repository.mark_queued(job_id)
            raise self.retry(exc=error, countdown=min(60 * (2**self.request.retries), 300))
        repository.fail(job_id, str(error))
        raise
    except (VideoProviderError, NotFoundError, ValueError) as error:
        repository.fail(job_id, str(error))
        raise
    except Exception as error:
        repository.fail(job_id, f"Unexpected animation generation error: {error}")
        raise
    finally:
        session.close()
