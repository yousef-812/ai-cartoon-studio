from __future__ import annotations

from typing import Protocol

from packages.scripts.models import (
    EpisodeScript,
    ScriptGenerationJobRead,
    ScriptGenerationRequest,
    ScriptReviewRequest,
)


class ScriptJobRepository(Protocol):
    def create(
        self,
        series_id: str,
        story_job_id: str,
        request: ScriptGenerationRequest,
        provider: str,
        model: str,
    ) -> ScriptGenerationJobRead: ...

    def get(self, job_id: str) -> ScriptGenerationJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[ScriptGenerationJobRead]: ...

    def mark_running(self, job_id: str) -> ScriptGenerationJobRead | None: ...

    def mark_queued(self, job_id: str) -> ScriptGenerationJobRead | None: ...

    def complete(self, job_id: str, result: EpisodeScript) -> ScriptGenerationJobRead | None: ...

    def fail(self, job_id: str, error: str) -> ScriptGenerationJobRead | None: ...

    def review(
        self, job_id: str, request: ScriptReviewRequest
    ) -> ScriptGenerationJobRead | None: ...
