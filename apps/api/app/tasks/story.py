import asyncio

from celery import Task

from app.db.session import SessionLocal
from app.llm_provider import build_llm_provider
from app.repositories.characters import SQLCharacterRepository
from app.repositories.series import SQLSeriesRepository
from app.repositories.stories import SQLStoryJobRepository
from app.worker import celery_app
from packages.agents.story_agent import StoryAgent
from packages.characters.service import CharacterService
from packages.common.errors import NotFoundError
from packages.llm.errors import LLMProviderError, LLMUnavailableError
from packages.series.service import SeriesService
from packages.stories.models import EpisodeStory


@celery_app.task(bind=True, max_retries=2, name="stories.generate")
def generate_story_job(self: Task, job_id: str) -> dict[str, object]:
    session = SessionLocal()
    jobs = SQLStoryJobRepository(session)
    try:
        job = jobs.get(job_id)
        if job is None:
            raise NotFoundError("Story generation job not found")
        jobs.mark_running(job_id)

        series_service = SeriesService(SQLSeriesRepository(session))
        character_service = CharacterService(SQLCharacterRepository(session))
        series = series_service.get(job.series_id)
        characters = character_service.list_for_series(job.series_id)
        locations = series_service.list_locations(job.series_id)

        agent = StoryAgent(build_llm_provider())
        payload = asyncio.run(
            agent.run(
                {
                    "series": series,
                    "characters": characters,
                    "locations": locations,
                    "request": job.request,
                }
            )
        )
        story = EpisodeStory.model_validate(payload)
        completed = jobs.complete(job_id, story)
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
        jobs.fail(job_id, f"Unexpected story generation error: {error}")
        raise
    finally:
        session.close()
