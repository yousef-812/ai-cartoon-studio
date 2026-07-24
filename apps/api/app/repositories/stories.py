from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import StoryGenerationJobRecord
from packages.stories.models import (
    EpisodeStory,
    StoryGenerationJobRead,
    StoryGenerationRequest,
    StoryJobStatus,
)


class SQLStoryJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: StoryGenerationJobRecord) -> StoryGenerationJobRead:
        result = (
            EpisodeStory.model_validate(record.result_payload)
            if record.result_payload is not None
            else None
        )
        return StoryGenerationJobRead(
            id=record.id,
            series_id=record.series_id,
            status=StoryJobStatus(record.status),
            provider=record.provider,
            model=record.model,
            attempts=record.attempts,
            request=StoryGenerationRequest.model_validate(record.request_payload),
            result=result,
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
        )

    def create(
        self,
        series_id: str,
        request: StoryGenerationRequest,
        provider: str,
        model: str,
    ) -> StoryGenerationJobRead:
        record = StoryGenerationJobRecord(
            series_id=series_id,
            status=StoryJobStatus.QUEUED.value,
            provider=provider,
            model=model,
            request_payload=request.model_dump(mode="json"),
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def get(self, job_id: str) -> StoryGenerationJobRead | None:
        record = self.session.get(StoryGenerationJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[StoryGenerationJobRead]:
        records = self.session.scalars(
            select(StoryGenerationJobRecord)
            .where(StoryGenerationJobRecord.series_id == series_id)
            .order_by(StoryGenerationJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def mark_running(self, job_id: str) -> StoryGenerationJobRead | None:
        record = self.session.get(StoryGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = StoryJobStatus.RUNNING.value
        record.attempts += 1
        record.error = None
        record.started_at = now
        record.completed_at = None
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_queued(self, job_id: str) -> StoryGenerationJobRead | None:
        record = self.session.get(StoryGenerationJobRecord, job_id)
        if record is None:
            return None
        record.status = StoryJobStatus.QUEUED.value
        record.error = None
        record.completed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(self, job_id: str, result: EpisodeStory) -> StoryGenerationJobRead | None:
        record = self.session.get(StoryGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = StoryJobStatus.SUCCEEDED.value
        record.result_payload = result.model_dump(mode="json")
        record.error = None
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(self, job_id: str, error: str) -> StoryGenerationJobRead | None:
        record = self.session.get(StoryGenerationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = StoryJobStatus.FAILED.value
        record.error = error[:8000]
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)
