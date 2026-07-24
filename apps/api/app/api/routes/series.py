from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_series_service
from packages.common.errors import ConflictError, NotFoundError
from packages.series.models import (
    LocationCreate,
    LocationRead,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)
from packages.series.service import SeriesService

router = APIRouter()


def _translate_domain_error(error: Exception) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, ConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("", response_model=SeriesRead, status_code=status.HTTP_201_CREATED)
def create_series(
    payload: SeriesCreate,
    service: SeriesService = Depends(get_series_service),
) -> SeriesRead:
    try:
        return service.create(payload)
    except (ConflictError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.get("", response_model=list[SeriesRead])
def list_series(service: SeriesService = Depends(get_series_service)) -> list[SeriesRead]:
    return service.list()


@router.get("/{series_id}", response_model=SeriesRead)
def get_series(
    series_id: str,
    service: SeriesService = Depends(get_series_service),
) -> SeriesRead:
    try:
        return service.get(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.patch("/{series_id}", response_model=SeriesRead)
def update_series(
    series_id: str,
    payload: SeriesUpdate,
    service: SeriesService = Depends(get_series_service),
) -> SeriesRead:
    try:
        return service.update(series_id, payload)
    except (ConflictError, NotFoundError, ValueError) as error:
        raise _translate_domain_error(error) from error


@router.post(
    "/{series_id}/locations",
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    series_id: str,
    payload: LocationCreate,
    service: SeriesService = Depends(get_series_service),
) -> LocationRead:
    try:
        return service.create_location(series_id, payload)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error


@router.get("/{series_id}/locations", response_model=list[LocationRead])
def list_locations(
    series_id: str,
    service: SeriesService = Depends(get_series_service),
) -> list[LocationRead]:
    try:
        return service.list_locations(series_id)
    except NotFoundError as error:
        raise _translate_domain_error(error) from error
