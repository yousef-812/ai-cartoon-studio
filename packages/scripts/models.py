from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class ScriptJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ScriptReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class ScriptGenerationRequest(BaseModel):
    target_duration_seconds: int | None = Field(default=None, ge=30, le=3600)
    dialogue_style: str = Field(
        default="natural, character-specific, and concise", min_length=3, max_length=500
    )
    pacing: str = Field(
        default="cinematic with clear escalation", min_length=3, max_length=300
    )
    constraints: list[str] = Field(default_factory=list, max_length=50)


class DialogueLine(BaseModel):
    order: int = Field(ge=1)
    speaker: str = Field(min_length=2, max_length=200)
    text: str = Field(min_length=1, max_length=1000)
    emotion: str = Field(min_length=2, max_length=200)
    delivery: str = Field(default="natural", min_length=2, max_length=300)
    action_before: str = Field(default="", max_length=1000)
    action_after: str = Field(default="", max_length=1000)
    pause_after_ms: int = Field(default=200, ge=0, le=5000)
    estimated_duration_seconds: float = Field(ge=0.2, le=60)


class ScriptScene(BaseModel):
    number: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    slugline: str = Field(min_length=3, max_length=300)
    location: str = Field(min_length=2, max_length=200)
    time_of_day: str = Field(min_length=2, max_length=100)
    characters: list[str] = Field(default_factory=list, max_length=20)
    objective: str = Field(min_length=5, max_length=1000)
    conflict: str = Field(min_length=5, max_length=1000)
    start_state: str = Field(min_length=5, max_length=1000)
    end_state: str = Field(min_length=5, max_length=1000)
    action_lines: list[str] = Field(default_factory=list, max_length=80)
    dialogue: list[DialogueLine] = Field(default_factory=list, max_length=100)
    estimated_duration_seconds: int = Field(ge=5, le=900)

    @model_validator(mode="after")
    def validate_dialogue_order(self) -> Self:
        orders = [line.order for line in self.dialogue]
        if orders and orders != list(range(1, len(orders) + 1)):
            raise ValueError("Dialogue line order must start at 1 and remain sequential")
        return self


class EpisodeScript(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    language: str = Field(min_length=2, max_length=40)
    target_duration_seconds: int = Field(ge=30, le=3600)
    total_estimated_duration_seconds: int = Field(ge=30, le=4200)
    cold_open: str = Field(min_length=10, max_length=1500)
    scenes: list[ScriptScene] = Field(min_length=3, max_length=60)
    closing_beat: str = Field(min_length=10, max_length=1500)
    continuity_updates: list[str] = Field(default_factory=list, max_length=50)
    production_notes: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_structure(self) -> Self:
        numbers = [scene.number for scene in self.scenes]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Scene numbers must start at 1 and remain sequential")

        scene_total = sum(scene.estimated_duration_seconds for scene in self.scenes)
        tolerance = max(10, round(self.total_estimated_duration_seconds * 0.1))
        if abs(scene_total - self.total_estimated_duration_seconds) > tolerance:
            raise ValueError(
                "Scene durations must approximately match total_estimated_duration_seconds"
            )
        return self


class ScriptReviewRequest(BaseModel):
    decision: ScriptReviewStatus
    notes: str = Field(default="", max_length=4000)


class ScriptGenerationJobRead(BaseModel):
    id: str
    series_id: str
    story_job_id: str
    status: ScriptJobStatus
    review_status: ScriptReviewStatus = ScriptReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    model: str
    attempts: int
    request: ScriptGenerationRequest
    result: EpisodeScript | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
