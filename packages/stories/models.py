from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class StoryJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class StoryReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class StoryGenerationRequest(BaseModel):
    premise: str = Field(min_length=10, max_length=3000)
    target_duration_seconds: int = Field(default=300, ge=30, le=3600)
    tone: str = Field(default="adventurous and emotionally warm", min_length=3, max_length=300)
    episode_number: int | None = Field(default=None, ge=1)
    constraints: list[str] = Field(default_factory=list, max_length=50)


class StoryBeat(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=10, max_length=1500)
    purpose: str = Field(min_length=3, max_length=500)


class SceneOutline(BaseModel):
    number: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    location: str = Field(min_length=2, max_length=200)
    characters: list[str] = Field(default_factory=list, max_length=20)
    objective: str = Field(min_length=5, max_length=1000)
    conflict: str = Field(min_length=5, max_length=1000)
    outcome: str = Field(min_length=5, max_length=1000)
    estimated_duration_seconds: int = Field(ge=5, le=900)


class EpisodeStory(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    logline: str = Field(min_length=10, max_length=500)
    theme: str = Field(min_length=3, max_length=300)
    hook: str = Field(min_length=10, max_length=1000)
    synopsis: str = Field(min_length=50, max_length=8000)
    beats: list[StoryBeat] = Field(min_length=3, max_length=20)
    scenes: list[SceneOutline] = Field(min_length=3, max_length=60)
    ending: str = Field(min_length=10, max_length=2000)
    continuity_updates: list[str] = Field(default_factory=list, max_length=50)
    safety_notes: list[str] = Field(default_factory=list, max_length=50)


class StoryReviewRequest(BaseModel):
    decision: StoryReviewStatus
    notes: str = Field(default="", max_length=4000)


class StoryGenerationJobRead(BaseModel):
    id: str
    series_id: str
    status: StoryJobStatus
    review_status: StoryReviewStatus = StoryReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    model: str
    attempts: int
    request: StoryGenerationRequest
    result: EpisodeStory | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
