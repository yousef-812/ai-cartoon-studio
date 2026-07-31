from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.asset_models import AnimationJobRecord
from packages.animations.models import (
    AnimatedShotSpec,
    AnimationJobRead,
    AnimationJobStatus,
    AnimationReviewRequest,
    AnimationReviewStatus,
)
from packages.videos.models import GeneratedVideo, VideoProviderResult


class SQLAnimationJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: AnimationJobRecord) -> AnimationJobRead:
        return AnimationJobRead(
            id=record.id,
            series_id=record.series_id,
            direction_job_id=record.direction_job_id,
            keyframe_asset_id=record.keyframe_asset_id,
            status=AnimationJobStatus(record.status),
            review_status=AnimationReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            attempts=record.attempts,
            provider_job_id=record.provider_job_id,
            spec=AnimatedShotSpec.model_validate(record.spec_payload),
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
        specs: list[AnimatedShotSpec],
        provider: str,
    ) -> list[AnimationJobRead]:
        existing = {
            record.animation_key: record
            for record in self.session.scalars(
                select(AnimationJobRecord).where(
                    AnimationJobRecord.direction_job_id == direction_job_id
                )
            ).all()
        }
        records: list[AnimationJobRecord] = []
        for spec in specs:
            record = existing.get(spec.key)
            if record is None:
                record = AnimationJobRecord(
                    series_id=series_id,
                    direction_job_id=direction_job_id,
                    keyframe_asset_id=spec.keyframe_asset_id,
                    animation_key=spec.key,
                    status=AnimationJobStatus.PLANNED.value,
                    review_status=AnimationReviewStatus.PENDING_REVIEW.value,
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

    def get(self, job_id: str) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[AnimationJobRead]:
        records = self.session.scalars(
            select(AnimationJobRecord)
            .where(AnimationJobRecord.series_id == series_id)
            .order_by(AnimationJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def list_for_direction(self, direction_job_id: str) -> list[AnimationJobRead]:
        records = self.session.scalars(
            select(AnimationJobRecord)
            .where(AnimationJobRecord.direction_job_id == direction_job_id)
            .order_by(AnimationJobRecord.animation_key)
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, job_id: str) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        if record is None:
            return None
        record.status = AnimationJobStatus.QUEUED.value
        record.review_status = AnimationReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.error = None
        record.provider_job_id = None
        record.videos_payload = []
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(self, job_id: str) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = AnimationJobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def set_provider_job(
        self,
        job_id: str,
        provider_job_id: str,
    ) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        if record is None:
            return None
        record.provider_job_id = provider_job_id
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(
        self,
        job_id: str,
        result: VideoProviderResult,
    ) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = AnimationJobStatus.SUCCEEDED.value
        record.review_status = AnimationReviewStatus.PENDING_REVIEW.value
        record.videos_payload = [video.model_dump(mode="json") for video in result.videos]
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = AnimationJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self,
        job_id: str,
        request: AnimationReviewRequest,
    ) -> AnimationJobRead | None:
        record = self.session.get(AnimationJobRecord, job_id)
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
