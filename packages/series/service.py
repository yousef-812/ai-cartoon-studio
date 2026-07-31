from __future__ import annotations

from packages.common.errors import ConflictError, NotFoundError
from packages.series.models import (
    LocationCreate,
    LocationRead,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)
from packages.series.repository import SeriesRepository
from packages.series.validators import slugify


class SeriesService:
    def __init__(self, repository: SeriesRepository) -> None:
        self.repository = repository

    def create(self, payload: SeriesCreate) -> SeriesRead:
        resolved_slug = slugify(payload.slug or payload.name)
        if self.repository.get_by_slug(resolved_slug) is not None:
            raise ConflictError(f"A series with slug '{resolved_slug}' already exists")
        return self.repository.create(payload, resolved_slug)

    def list(self) -> list[SeriesRead]:
        return self.repository.list()

    def get(self, series_id: str) -> SeriesRead:
        series = self.repository.get(series_id)
        if series is None:
            raise NotFoundError("Series not found")
        return series

    def update(self, series_id: str, payload: SeriesUpdate) -> SeriesRead:
        if payload.slug is not None:
            resolved_slug = slugify(payload.slug)
            existing = self.repository.get_by_slug(resolved_slug)
            if existing is not None and existing.id != series_id:
                raise ConflictError(f"A series with slug '{resolved_slug}' already exists")
            payload = payload.model_copy(update={"slug": resolved_slug})

        series = self.repository.update(series_id, payload)
        if series is None:
            raise NotFoundError("Series not found")
        return series

    def create_location(self, series_id: str, payload: LocationCreate) -> LocationRead:
        self.get(series_id)
        return self.repository.create_location(series_id, payload)

    def list_locations(self, series_id: str) -> list[LocationRead]:
        self.get(series_id)
        return self.repository.list_locations(series_id)
