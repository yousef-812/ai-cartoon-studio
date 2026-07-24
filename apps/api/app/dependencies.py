from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.llm_provider import build_llm_provider
from app.repositories.characters import SQLCharacterRepository
from app.repositories.scripts import SQLScriptJobRepository
from app.repositories.series import SQLSeriesRepository
from app.repositories.stories import SQLStoryJobRepository
from packages.characters.service import CharacterService
from packages.llm.openai_compatible import OpenAICompatibleLLMProvider
from packages.scripts.service import ScriptJobService
from packages.series.service import SeriesService
from packages.stories.service import StoryJobService


def get_series_service(session: Session = Depends(get_db)) -> SeriesService:
    return SeriesService(SQLSeriesRepository(session))


def get_character_service(session: Session = Depends(get_db)) -> CharacterService:
    return CharacterService(SQLCharacterRepository(session))


def get_story_job_service(session: Session = Depends(get_db)) -> StoryJobService:
    return StoryJobService(SQLStoryJobRepository(session))


def get_script_job_service(session: Session = Depends(get_db)) -> ScriptJobService:
    return ScriptJobService(SQLScriptJobRepository(session))


def get_llm_provider() -> OpenAICompatibleLLMProvider:
    return build_llm_provider()
