from typing import Protocol

from packages.stories.models import (
    EpisodeStory,
    StoryGenerationJobRead,
    StoryGenerationRequest,
    StoryReviewRequest,
)


class StoryJobRepository(Protocol):
    def create(
        self,
        series_id: str,
        request: StoryGenerationRequest,
        provider: str,
        model: str,
    ) -> StoryGenerationJobRead: ...

    def get(self, job_id: str) -> StoryGenerationJobRead | None: ...

    def list_for_series(self, series_id: str) -> list[StoryGenerationJobRead]: ...

    def mark_running(self, job_id: str) -> StoryGenerationJobRead | None: ...

    def mark_queued(self, job_id: str) -> StoryGenerationJobRead | None: ...

    def complete(self, job_id: str, result: EpisodeStory) -> StoryGenerationJobRead | None: ...

    def fail(self, job_id: str, error: str) -> StoryGenerationJobRead | None: ...

    def review(
        self, job_id: str, request: StoryReviewRequest
    ) -> StoryGenerationJobRead | None: ...
