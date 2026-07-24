from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.characters import SQLCharacterRepository
from app.repositories.series import SQLSeriesRepository
from packages.characters.service import CharacterService
from packages.series.service import SeriesService


def get_series_service(session: Session = Depends(get_db)) -> SeriesService:
    return SeriesService(SQLSeriesRepository(session))


def get_character_service(session: Session = Depends(get_db)) -> CharacterService:
    return CharacterService(SQLCharacterRepository(session))
