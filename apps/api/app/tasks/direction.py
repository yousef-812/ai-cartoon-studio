import asyncio

from celery import Task

from app.db.session import SessionLocal
from app.llm_provider import build_llm_provider
from app.repositories.characters import SQLCharacterRepository
from app.repositories.directions import SQLDirectionJobRepository
from app.repositories.scripts import SQLScriptJobRepository
from app.repositories.series import SQLSeriesRepository
from app.worker import celery_app
from packages.agents.director_agent import DirectorAgent
from packages.characters.service import CharacterService
from packages.common.errors import NotFoundError
from packages.direction.models import EpisodeDirection
from packages.llm.errors import LLMProviderError, LLMUnavailableError
from packages.series.service import SeriesService


@celery_app.task(bind=True, max_retries=2, name="directions.generate")
def generate_direction_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    jobs = SQLDirectionJobRepository(session)
    try:
        job = jobs.get(job_id)
        if job is None:
            raise NotFoundError("Direction generation job not found")
        jobs.mark_running(job_id)

        script_job = SQLScriptJobRepository(session).get(job.script_job_id)
        if script_job is None or script_job.result is None:
            raise NotFoundError("Approved screenplay result not found")

        series_service = SeriesService(SQLSeriesRepository(session))
        character_service = CharacterService(SQLCharacterRepository(session))
        series = series_service.get(job.series_id)
        characters = character_service.list_for_series(job.series_id)
        locations = series_service.list_locations(job.series_id)

        agent = DirectorAgent(build_llm_provider())
        payload = asyncio.run(
            agent.run(
                {
                    "series": series,
                    "characters": characters,
                    "locations": locations,
                    "script": script_job.result,
                    "request": job.request,
                }
            )
        )
        direction = EpisodeDirection.model_validate(payload)
        completed = jobs.complete(job_id, direction)
        return completed.model_dump(mode="json") if completed else payload
    except LLMUnavailableError as error:
        if self.request.retries < self.max_retries:
            jobs.mark_queued(job_id)
            raise self.retry(exc=error, countdown=min(30 * (2**self.request.retries), 180))
        jobs.fail(job_id, str(error))
        raise
    except (LLMProviderError, NotFoundError, ValueError) as error:
        jobs.fail(job_id, str(error))
        raise
    except Exception as error:
        jobs.fail(job_id, f"Unexpected direction generation error: {error}")
        raise
    finally:
        session.close()
