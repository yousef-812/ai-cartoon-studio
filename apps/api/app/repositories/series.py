from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LocationRecord, SeriesRecord
from packages.series.models import (
    LocationCreate,
    LocationRead,
    SeriesCreate,
    SeriesRead,
    SeriesUpdate,
)


class SQLSeriesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: SeriesRecord) -> SeriesRead:
        return SeriesRead.model_validate(record)

    @staticmethod
    def _location_to_read(record: LocationRecord) -> LocationRead:
        return LocationRead.model_validate(record)

    def create(self, payload: SeriesCreate, slug: str) -> SeriesRead:
        record = SeriesRecord(
            name=payload.name,
            slug=slug,
            logline=payload.logline,
            synopsis=payload.synopsis,
            genre=payload.genre,
            target_audience=payload.target_audience,
            primary_language=payload.primary_language,
            status=payload.status.value,
            visual_style=payload.visual_style.model_dump(mode="json"),
            rules=payload.rules.model_dump(mode="json"),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def list(self) -> list[SeriesRead]:
        records = self.session.scalars(
            select(SeriesRecord).order_by(SeriesRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def get(self, series_id: str) -> SeriesRead | None:
        record = self.session.get(SeriesRecord, series_id)
        return self._to_read(record) if record is not None else None

    def get_by_slug(self, slug: str) -> SeriesRead | None:
        record = self.session.scalar(select(SeriesRecord).where(SeriesRecord.slug == slug))
        return self._to_read(record) if record is not None else None

    def update(self, series_id: str, payload: SeriesUpdate) -> SeriesRead | None:
        record = self.session.get(SeriesRecord, series_id)
        if record is None:
            return None

        changes = payload.model_dump(exclude_unset=True, mode="json")
        for field, value in changes.items():
            if field == "status" and value is not None:
                value = str(value)
            setattr(record, field, value)
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def create_location(self, series_id: str, payload: LocationCreate) -> LocationRead:
        record = LocationRecord(
            series_id=series_id,
            name=payload.name,
            description=payload.description,
            visual_prompt=payload.visual_prompt,
            rules=payload.rules,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._location_to_read(record)

    def list_locations(self, series_id: str) -> list[LocationRead]:
        records = self.session.scalars(
            select(LocationRecord)
            .where(LocationRecord.series_id == series_id)
            .order_by(LocationRecord.name)
        ).all()
        return [self._location_to_read(record) for record in records]
