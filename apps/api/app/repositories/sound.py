from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.sound_models import SoundMixJobRecord
from packages.sound.models import (
    GeneratedSoundAsset,
    SoundMixJobRead,
    SoundMixJobSpec,
    SoundMixJobStatus,
    SoundMixReviewRequest,
    SoundMixReviewStatus,
)
from packages.videos.models import GeneratedVideo


class SQLSoundMixJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: SoundMixJobRecord) -> SoundMixJobRead:
        return SoundMixJobRead(
            id=record.id,
            series_id=record.series_id,
            direction_job_id=record.direction_job_id,
            source_job_type=record.source_job_type,
            source_job_id=record.source_job_id,
            status=SoundMixJobStatus(record.status),
            review_status=SoundMixReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            attempts=record.attempts,
            spec=SoundMixJobSpec.model_validate(record.spec_payload),
            assets=[GeneratedSoundAsset.model_validate(item) for item in record.assets_payload],
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
        specs: list[SoundMixJobSpec],
        provider: str,
    ) -> list[SoundMixJobRead]:
        existing = {
            record.sound_key: record
            for record in self.session.scalars(
                select(SoundMixJobRecord).where(
                    SoundMixJobRecord.direction_job_id == direction_job_id
                )
            ).all()
        }
        records: list[SoundMixJobRecord] = []
        for spec in specs:
            record = existing.get(spec.key)
            if record is None:
                record = SoundMixJobRecord(
                    series_id=series_id,
                    direction_job_id=direction_job_id,
                    source_job_type=spec.source_job_type,
                    source_job_id=spec.source_job_id,
                    sound_key=spec.key,
                    status=SoundMixJobStatus.PLANNED.value,
                    review_status=SoundMixReviewStatus.PENDING_REVIEW.value,
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

    def get(self, job_id: str) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[SoundMixJobRead]:
        records = self.session.scalars(
            select(SoundMixJobRecord)
            .where(SoundMixJobRecord.series_id == series_id)
            .order_by(SoundMixJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def list_for_direction(self, direction_job_id: str) -> list[SoundMixJobRead]:
        records = self.session.scalars(
            select(SoundMixJobRecord)
            .where(SoundMixJobRecord.direction_job_id == direction_job_id)
            .order_by(SoundMixJobRecord.sound_key)
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, job_id: str) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
        if record is None:
            return None
        record.status = SoundMixJobStatus.QUEUED.value
        record.review_status = SoundMixReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.assets_payload = []
        record.videos_payload = []
        record.error = None
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(self, job_id: str) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = SoundMixJobStatus.RUNNING.value
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
        assets: list[GeneratedSoundAsset],
        video: GeneratedVideo,
    ) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = SoundMixJobStatus.SUCCEEDED.value
        record.review_status = SoundMixReviewStatus.PENDING_REVIEW.value
        record.assets_payload = [asset.model_dump(mode="json") for asset in assets]
        record.videos_payload = [video.model_dump(mode="json")]
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = SoundMixJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self,
        job_id: str,
        request: SoundMixReviewRequest,
    ) -> SoundMixJobRead | None:
        record = self.session.get(SoundMixJobRecord, job_id)
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
