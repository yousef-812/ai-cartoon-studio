import asyncio

from celery import Task

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.sound import SQLSoundMixJobRepository
from app.sound_provider import build_sound_provider
from app.worker import celery_app
from packages.common.errors import NotFoundError
from packages.mixing.ffmpeg import FFmpegSoundMixer
from packages.sound.errors import (
    SoundMixError,
    SoundMixUnavailableError,
    SoundProviderError,
    SoundProviderUnavailableError,
)
from packages.sound.storage import SoundArtifactStore


@celery_app.task(bind=True, max_retries=2, name="sound.generate_mix")
def generate_sound_mix_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    repository = SQLSoundMixJobRepository(session)
    try:
        job = repository.get(job_id)
        if job is None:
            raise NotFoundError("Sound mix job not found")
        repository.mark_running(job_id)

        provider = build_sound_provider()
        store = SoundArtifactStore(settings.storage_path)
        assets = []
        for index, cue in enumerate(job.spec.generation.cues, start=1):
            rendered = asyncio.run(provider.generate(cue))
            assets.append(
                store.persist_asset(
                    rendered,
                    cue,
                    series_id=job.series_id,
                    job_id=job.id,
                    index=index,
                )
            )

        rendered_mix = FFmpegSoundMixer(settings.ffmpeg_binary).mix(
            job.spec.generation,
            assets,
        )
        video = store.persist_mix(
            rendered_mix,
            series_id=job.series_id,
            job_id=job.id,
        )
        completed = repository.complete(job_id, assets, video)
        return completed.model_dump(mode="json") if completed else video.model_dump(mode="json")
    except (SoundProviderUnavailableError, SoundMixUnavailableError) as error:
        if self.request.retries < self.max_retries:
            repository.mark_queued(job_id)
            raise self.retry(exc=error, countdown=min(30 * (2**self.request.retries), 180))
        repository.fail(job_id, str(error))
        raise
    except (SoundProviderError, SoundMixError, NotFoundError, ValueError) as error:
        repository.fail(job_id, str(error))
        raise
    except Exception as error:
        repository.fail(job_id, f"Unexpected sound design error: {error}")
        raise
    finally:
        session.close()
