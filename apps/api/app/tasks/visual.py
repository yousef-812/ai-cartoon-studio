import asyncio

from celery import Task

from app.core.config import settings
from app.db.session import SessionLocal
from app.image_provider import build_image_provider
from app.repositories.visuals import SQLVisualAssetRepository
from app.worker import celery_app
from packages.artifacts.local_store import LocalArtifactStore
from packages.common.errors import NotFoundError
from packages.images.errors import ImageProviderError, ImageProviderUnavailableError


@celery_app.task(bind=True, max_retries=2, name="visuals.generate")
def generate_visual_asset(self: Task, asset_id: str) -> dict[str, object]:
    session = SessionLocal()
    repository = SQLVisualAssetRepository(session)
    try:
        asset = repository.get(asset_id)
        if asset is None:
            raise NotFoundError("Visual asset not found")
        repository.mark_running(asset_id)

        provider = build_image_provider()
        submission = asyncio.run(provider.submit(asset.spec.generation))
        repository.set_provider_job(asset_id, submission.provider_job_id)
        result = asyncio.run(provider.wait_for_result(submission.provider_job_id))
        store = LocalArtifactStore(
            settings.storage_path,
            allowed_base_url=settings.image_base_url,
            timeout_seconds=settings.image_timeout_seconds,
        )
        durable_result = asyncio.run(
            store.persist_result(
                result,
                series_id=asset.series_id,
                asset_id=asset.id,
            )
        )
        completed = repository.complete(asset_id, durable_result)
        return (
            completed.model_dump(mode="json")
            if completed
            else durable_result.model_dump(mode="json")
        )
    except ImageProviderUnavailableError as error:
        if self.request.retries < self.max_retries:
            repository.mark_queued(asset_id)
            raise self.retry(exc=error, countdown=min(45 * (2**self.request.retries), 240))
        repository.fail(asset_id, str(error))
        raise
    except (ImageProviderError, NotFoundError, ValueError) as error:
        repository.fail(asset_id, str(error))
        raise
    except Exception as error:
        repository.fail(asset_id, f"Unexpected visual generation error: {error}")
        raise
    finally:
        session.close()
