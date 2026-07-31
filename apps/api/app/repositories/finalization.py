from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.finalization_models import FinalizationJobRecord
from packages.finalization.models import (
    FinalArtifact,
    FinalizationJobRead,
    FinalizationJobSpec,
    FinalizationJobStatus,
    FinalizationReviewRequest,
    FinalizationReviewStatus,
    QCReport,
)


class SQLFinalizationJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_read(record: FinalizationJobRecord) -> FinalizationJobRead:
        return FinalizationJobRead(
            id=record.id,
            series_id=record.series_id,
            direction_job_id=record.direction_job_id,
            status=FinalizationJobStatus(record.status),
            review_status=FinalizationReviewStatus(record.review_status),
            review_notes=record.review_notes,
            attempts=record.attempts,
            spec=FinalizationJobSpec.model_validate(record.spec_payload),
            report=QCReport.model_validate(record.report_payload) if record.report_payload else None,
            artifacts=[FinalArtifact.model_validate(item) for item in record.artifacts_payload],
            error=record.error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            started_at=record.started_at,
            completed_at=record.completed_at,
            reviewed_at=record.reviewed_at,
        )

    def create(self, series_id: str, spec: FinalizationJobSpec) -> FinalizationJobRead:
        existing = self.session.scalar(
            select(FinalizationJobRecord).where(
                FinalizationJobRecord.direction_job_id == spec.direction_job_id
            )
        )
        if existing is not None:
            existing.spec_payload = spec.model_dump(mode="json")
            existing.status = FinalizationJobStatus.PLANNED.value
            existing.review_status = FinalizationReviewStatus.PENDING_REVIEW.value
            existing.review_notes = ""
            existing.report_payload = None
            existing.artifacts_payload = []
            existing.error = None
            existing.updated_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(existing)
            return self._to_read(existing)
        record = FinalizationJobRecord(
            series_id=series_id,
            direction_job_id=spec.direction_job_id,
            status=FinalizationJobStatus.PLANNED.value,
            review_status=FinalizationReviewStatus.PENDING_REVIEW.value,
            spec_payload=spec.model_dump(mode="json"),
        )
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(
                select(FinalizationJobRecord).where(
                    FinalizationJobRecord.direction_job_id == spec.direction_job_id
                )
            )
            if existing is None:
                raise
            return self._to_read(existing)
        self.session.refresh(record)
        return self._to_read(record)

    def get(self, job_id: str) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
        return self._to_read(record) if record is not None else None

    def list_for_series(self, series_id: str) -> list[FinalizationJobRead]:
        records = self.session.scalars(
            select(FinalizationJobRecord)
            .where(FinalizationJobRecord.series_id == series_id)
            .order_by(FinalizationJobRecord.created_at.desc())
        ).all()
        return [self._to_read(record) for record in records]

    def mark_queued(self, job_id: str) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
        if record is None:
            return None
        record.status = FinalizationJobStatus.QUEUED.value
        record.review_status = FinalizationReviewStatus.PENDING_REVIEW.value
        record.review_notes = ""
        record.report_payload = None
        record.artifacts_payload = []
        record.error = None
        record.completed_at = None
        record.reviewed_at = None
        record.updated_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def mark_running(self, job_id: str) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = FinalizationJobStatus.RUNNING.value
        record.attempts += 1
        record.started_at = now
        record.updated_at = now
        record.error = None
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def complete(
        self,
        job_id: str,
        report: QCReport,
        artifacts: list[FinalArtifact],
    ) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = FinalizationJobStatus.SUCCEEDED.value
        record.review_status = FinalizationReviewStatus.PENDING_REVIEW.value
        record.report_payload = report.model_dump(mode="json")
        record.artifacts_payload = [artifact.model_dump(mode="json") for artifact in artifacts]
        record.error = None
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def fail(
        self,
        job_id: str,
        error: str,
        report: QCReport | None = None,
    ) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
        if record is None:
            return None
        now = datetime.now(UTC)
        record.status = FinalizationJobStatus.FAILED.value
        record.error = error[:8000]
        record.report_payload = report.model_dump(mode="json") if report else None
        record.completed_at = now
        record.updated_at = now
        self.session.commit()
        self.session.refresh(record)
        return self._to_read(record)

    def review(
        self,
        job_id: str,
        request: FinalizationReviewRequest,
    ) -> FinalizationJobRead | None:
        record = self.session.get(FinalizationJobRecord, job_id)
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
