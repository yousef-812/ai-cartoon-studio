from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.asset_models import VisualAssetRecord
from packages.images.models import GeneratedImage, ImageProviderResult
from packages.visuals.models import (
    VisualAssetRead,
    VisualAssetReviewRequest,
    VisualAssetReviewStatus,
    VisualAssetSpec,
    VisualAssetStatus,
)


class SQLVisualAssetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: VisualAssetRecord) -> VisualAssetRead:
        return VisualAssetRead(
            id=record.id,
            series_id=record.series_id,
            direction_job_id=record.direction_job_id,
            status=VisualAssetStatus(record.status),
            review_status=VisualAssetReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            attempts=record.attempts,
            provider_job_id=record.provider_job_id,
            spec=VisualAssetSpec.model_validate(record.spec_payload),
            images=[GeneratedImage.model_validate(item) for item in record.images_payload],
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            reviewed_at=record.reviewed_at,
        )

    def create_many(
        self,
        series_id: str,
        direction_job_id: str,
        specs: list[VisualAssetSpec],
        provider: str,
    ) -> list[VisualAssetRead]:
        existing = {
            record.asset_key: record
            for record in self.session.scalars(
                select(VisualAssetRecord).where(
                    VisualAssetRecord.direction_job_id == direction_job_id
                )
            ).all()
        }
        records: list[VisualAssetRecord] = []
        for spec in specs:
            record = existing.get(spec.key)
            if record is None:
                initial_status = (
                    VisualAssetStatus.BLOCKED.value
                    if spec.dependency_keys
                    else VisualAssetStatus.PLANNED.value
                )
                record = VisualAssetRecord(
                    series_id=series_id,
                    direction_job_id=direction_job_id,
                    asset_key=spec.key,
                    asset_type=spec.asset_type.value,
                    status=initial_status,
                    review_status=VisualAssetReviewStatus.PENDING_REVIEW.value,
                    provider=provider,
                    spec_payload=spec.model_dump(mode="json"),
                )
                self.session.add(record)
            records.append(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return self.list_for_direction(direction_job_id)
        for record in records:
            self.session.refresh(record)
        return [self._to_read(record) for record in records]

    def get(self, asset_id: str) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        return self._to_read(record) if record is not None else None

    def get_by_key(self, direction_job_id: str, key: str) -> VisualAssetRead | None:
        record = self.session.scalar(
            select(VisualAssetRecord).where(
                VisualAssetRecord.direction_job_id == direction_job_id,
                VisualAssetRecord.asset_key == key,
            )
        )
        return self._to_read(record) if record is not None else None

    def list_for_direction(self, direction_job_id: str) -> list[VisualAssetRead]:
        records = self.session.scalars(
            select(VisualAssetRecord)
            .where(VisualAssetRecord.direction_job_id == direction_job_id)
            .order_by(VisualAssetRecord.asset_type, VisualAssetRecord.asset_key)
        ).all()
        return [self._to_read(record) for record in records]

    def list_for_series(self, series_id: str) -> list[VisualAssetRead]:
        records = self.session.scalars(
            select(VisualAssetRecord)
            .where(VisualAssetRecord.series_id == series_id)
            .order_by(VisualAssetRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, asset_id: str) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        record.status = VisualAssetStatus.QUEUED.value
        record.review_status = VisualAssetReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.error = None
        record.provider_job_id = None
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(
        self, asset_id: str, provider_job_id: str | None = None
    ) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VisualAssetStatus.RUNNING.value
        record.attempts += 1
        record.provider_job_id = provider_job_id or record.provider_job_id
        record.error = None
        record.started_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def set_provider_job(
        self, asset_id: str, provider_job_id: str
    ) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        record.provider_job_id = provider_job_id
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(
        self, asset_id: str, result: ImageProviderResult
    ) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VisualAssetStatus.SUCCEEDED.value
        record.review_status = VisualAssetReviewStatus.PENDING_REVIEW.value
        record.images_payload = [image.model_dump(mode="json") for image in result.images]
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, asset_id: str, error: str) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VisualAssetStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self, asset_id: str, request: VisualAssetReviewRequest
    ) -> VisualAssetRead | None:
        record = self.session.get(VisualAssetRecord, asset_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.review_status = request.decision.value
        record.review_notes = request.notes
        record.reviewed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)
