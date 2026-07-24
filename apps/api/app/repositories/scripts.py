from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ScriptGenerationJobRecord
from packages.scripts.models import (
    EpisodeScript,
    ScriptGenerationJobRead,
    ScriptGenerationRequest,
    ScriptJobStatus,
    ScriptReviewRequest,
    ScriptReviewStatus,
)


class SQLScriptJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: ScriptGenerationJobRecord) -> ScriptGenerationJobRead:
        result = (
            EpisodeScript.model_validate(record.result_payload)
            if record.result_payload is not None
            else None
        )
        return ScriptGenerationJobRead(
            id=record.id,
            series_id=record.series_id,
            story_job_id=record.story_job_id,
            status=ScriptJobStatus(record.status),
            review_status=ScriptReviewStatus(record.review_status),
            review_notes=record.review_notes,
            provider=record.provider,
            model=record.model,
            attempts=record.attempts,
            request=ScriptGenerationRequest.model_validate(record.request_payload),
            result=result,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            reviewed_at=record.reviewed_at,
        )

    def create(
        self,
        series_id: str,
        story_job_id: str,
        request: ScriptGenerationRequest,
        provider: str,
        model: str,
    ) -> ScriptGenerationJobRead:
        record = ScriptGenerationJobRecord(
            series_id=series_id,
            story_job_id=story_job_id,
            status=ScriptJobStatus.QUEUED.value,
            review_status=ScriptReviewStatus.PENDING_REVIEW.value,
            provider=provider,
            model=model,
            request_payload=request.model_dump(mode="json"),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def get(self, job_id: str) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[ScriptGenerationJobRead]:
        records = self.session.scalars(
            select(ScriptGenerationJobRecord)
            .where(ScriptGenerationJobRecord.series_id == series_id)
            .order_by(ScriptGenerationJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def mark_running(self, job_id: str) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = ScriptJobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = now
        record.completed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_queued(self, job_id: str) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
        if record is None:
            return None
        record.status = ScriptJobStatus.QUEUED.value
        record.review_status = ScriptReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.error = None
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(self, job_id: str, result: EpisodeScript) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = ScriptJobStatus.SUCCEEDED.value
        record.review_status = ScriptReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.result_payload = result.model_dump(mode="json")
        record.error = None
        record.completed_at = now
        record.reviewed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = ScriptJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self, job_id: str, request: ScriptReviewRequest
    ) -> ScriptGenerationJobRead | None:
        record = self.session.get(ScriptGenerationJobRecord, job_id)
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
