from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.asset_models import VoiceLineJobRecord
from packages.audio.models import GeneratedAudio
from packages.voices.models import (
    VoiceJobRead,
    VoiceJobStatus,
    VoiceLineSpec,
    VoiceReviewRequest,
    VoiceReviewStatus,
)


class SQLVoiceJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: VoiceLineJobRecord) -> VoiceJobRead:
        audio = (
            GeneratedAudio.model_validate(record.audio_payload)
            if record.audio_payload is not None
            else None
        )
        return VoiceJobRead(
            id=record.id,
            series_id=record.series_id,
            script_job_id=record.script_job_id,
            character_id=record.character_id,
            status=VoiceJobStatus(record.status),
            review_status=VoiceReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            attempts=record.attempts,
            spec=VoiceLineSpec.model_validate(record.spec_payload),
            audio=audio,
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
        script_job_id: str,
        specs: list[VoiceLineSpec],
        provider: str,
    ) -> list[VoiceJobRead]:
        existing = {
            record.voice_key: record
            for record in self.session.scalars(
                select(VoiceLineJobRecord).where(
                    VoiceLineJobRecord.script_job_id == script_job_id
                )
            ).all()
        }
        records: list[VoiceLineJobRecord] = []
        for spec in specs:
            record = existing.get(spec.key)
            if record is None:
                record = VoiceLineJobRecord(
                    series_id=series_id,
                    script_job_id=script_job_id,
                    character_id=spec.character_id,
                    voice_key=spec.key,
                    status=VoiceJobStatus.PLANNED.value,
                    review_status=VoiceReviewStatus.PENDING_REVIEW.value,
                    provider=provider,
                    spec_payload=spec.model_dump(mode="json"),
                )
                self.session.add(record)
            records.append(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return self.list_for_script(script_job_id)
        for record in records:
            self.session.refresh(record)
        return [self._to_read(record) for record in records]

    def get(self, job_id: str) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[VoiceJobRead]:
        records = self.session.scalars(
            select(VoiceLineJobRecord)
            .where(VoiceLineJobRecord.series_id == series_id)
            .order_by(VoiceLineJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def list_for_script(self, script_job_id: str) -> list[VoiceJobRead]:
        records = self.session.scalars(
            select(VoiceLineJobRecord)
            .where(VoiceLineJobRecord.script_job_id == script_job_id)
            .order_by(VoiceLineJobRecord.voice_key)
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, job_id: str) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
        if record is None:
            return None
        record.status = VoiceJobStatus.QUEUED.value
        record.review_status = VoiceReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.audio_payload = None
        record.error = None
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(self, job_id: str) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VoiceJobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(self, job_id: str, audio: GeneratedAudio) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VoiceJobStatus.SUCCEEDED.value
        record.review_status = VoiceReviewStatus.PENDING_REVIEW.value
        record.audio_payload = audio.model_dump(mode="json")
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = VoiceJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(self, job_id: str, request: VoiceReviewRequest) -> VoiceJobRead | None:
        record = self.session.get(VoiceLineJobRecord, job_id)
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
