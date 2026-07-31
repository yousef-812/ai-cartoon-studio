from __future__ import annotations

from typing import Protocol

from packages.series.models import (
    LocationCreate,
    LocationRead,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)


class SeriesRepository(Protocol):
    def create(self, payload: SeriesCreate, slug: str) -> SeriesRead: ...

    def list(self) -> list[SeriesRead]: ...

    def get(self, series_id: str) -> SeriesRead | None: ...

    def get_by_slug(self, slug: str) -> SeriesRead | None: ...

    def update(self, series_id: str, payload: SeriesUpdate) -> SeriesRead | None: ...

    def create_location(self, series_id: str, payload: LocationCreate) -> LocationRead: ...

    def list_locations(self, series_id: str) -> list[LocationRead]: ...
