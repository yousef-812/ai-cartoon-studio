from typing import Protocol

from packages.finalization.models import (
    FinalArtifact,
    FinalizationJobRead,
    FinalizationJobSpec,
    FinalizationReviewRequest,
    QCReport,
)


class FinalizationJobRepository(Protocol):
    def create(self, series_id: str, spec: FinalizationJobSpec) -> FinalizationJobRead: ...

    def get(self, job_id: str) -> FinalizationJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[FinalizationJobRead]: ...

    def mark_queued(self, job_id: str) -> FinalizationJobRead | None: ...

    def mark_running(self, job_id: str) -> FinalizationJobRead | None: ...

    def complete(
        self,
        job_id: str,
        report: QCReport,
        artifacts: list[FinalArtifact],
    ) -> FinalizationJobRead | None: ...

    def fail(self, job_id: str, error: str, report: QCReport | None = None) -> FinalizationJobRead | None: ...

    def review(
        self,
        job_id: str,
        request: FinalizationReviewRequest,
    ) -> FinalizationJobRead | None: ...
