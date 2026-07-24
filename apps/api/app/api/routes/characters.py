from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_character_service, get_series_service
from packages.characters.models import CharacterCreate, CharacterRead, CharacterUpdate
from packages.characters.service import CharacterService
from packages.common.errors import ConflictError, NotFoundError
from packages.series.service import SeriesService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post(
    "/series/{series_id}/characters",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_character(
    series_id: str,
    payload: CharacterCreate,
    character_service: CharacterService = Depends(get_character_service),
    series_service: SeriesService = Depends(get_series_service),
) -> CharacterRead:
    try:
        series_service.get(series_id)
        return character_service.create(series_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error


@router.get("/series/{series_id}/characters", response_model=list[CharacterRead])
def list_characters(
    series_id: str,
    character_service: CharacterService = Depends(get_character_service),
    series_service: SeriesService = Depends(get_series_service),
) -> list[CharacterRead]:
    try:
        series_service.get(series_id)
        return character_service.list_for_series(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/characters/{character_id}", response_model=CharacterRead)
def get_character(
    character_id: str,
    service: CharacterService = Depends(get_character_service),
) -> CharacterRead:
    try:
        return service.get(character_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.patch("/characters/{character_id}", response_model=CharacterRead)
def update_character(
    character_id: str,
    payload: CharacterUpdate,
    service: CharacterService = Depends(get_character_service),
) -> CharacterRead:
    try:
        return service.update(character_id, payload)
    except (ConflictError, NotFoundError) as error:
        raise _translate_domain_error(error) from error
