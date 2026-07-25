from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.asset_models import LipSyncJobRecord
from packages.lipsync.models import (
    LipSyncJobRead,
    LipSyncJobStatus,
    LipSyncReviewRequest,
    LipSyncReviewStatus,
    LipSyncShotSpec,
)
from packages.videos.models import GeneratedVideo, VideoProviderResult


class SQLLipSyncJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: LipSyncJobRecord) -> LipSyncJobRead:
        return LipSyncJobRead(
            id=record.id,
            series_id=record.series_id,
            direction_job_id=record.direction_job_id,
            animation_job_id=record.animation_job_id,
            status=LipSyncJobStatus(record.status),
            review_status=LipSyncReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            attempts=record.attempts,
            spec=LipSyncShotSpec.model_validate(record.spec_payload),
            videos=[GeneratedVideo.model_validate(item) for item in record.videos_payload],
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
        specs: list[LipSyncShotSpec],
        provider: str,
    ) -> list[LipSyncJobRead]:
        existing = {
            record.lip_sync_key: record
            for record in self.session.scalars(
                select(LipSyncJobRecord).where(
                    LipSyncJobRecord.direction_job_id == direction_job_id
                )
            ).all()
        }
        records: list[LipSyncJobRecord] = []
        for spec in specs:
            record = existing.get(spec.key)
            if record is None:
                record = LipSyncJobRecord(
                    series_id=series_id,
                    direction_job_id=direction_job_id,
                    animation_job_id=spec.animation_job_id,
                    lip_sync_key=spec.key,
                    status=LipSyncJobStatus.PLANNED.value,
                    review_status=LipSyncReviewStatus.PENDING_REVIEW.value,
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

    def get(self, job_id: str) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[LipSyncJobRead]:
        records = self.session.scalars(
            select(LipSyncJobRecord)
            .where(LipSyncJobRecord.series_id == series_id)
            .order_by(LipSyncJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def list_for_direction(self, direction_job_id: str) -> list[LipSyncJobRead]:
        records = self.session.scalars(
            select(LipSyncJobRecord)
            .where(LipSyncJobRecord.direction_job_id == direction_job_id)
            .order_by(LipSyncJobRecord.lip_sync_key)
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, job_id: str) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
        if record is None:
            return None
        record.status = LipSyncJobStatus.QUEUED.value
        record.review_status = LipSyncReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.error = None
        record.videos_payload = []
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(self, job_id: str) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = LipSyncJobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(
        self,
        job_id: str,
        result: VideoProviderResult,
    ) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = LipSyncJobStatus.SUCCEEDED.value
        record.review_status = LipSyncReviewStatus.PENDING_REVIEW.value
        record.videos_payload = [video.model_dump(mode="json") for video in result.videos]
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = LipSyncJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self,
        job_id: str,
        request: LipSyncReviewRequest,
    ) -> LipSyncJobRead | None:
        record = self.session.get(LipSyncJobRecord, job_id)
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
