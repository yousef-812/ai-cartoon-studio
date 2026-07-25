from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class DirectionJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class DirectionReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class DirectionGenerationRequest(BaseModel):
    min_shot_duration_seconds: float = Field(default=0.5, ge=0.5, le=30.0)
    max_shot_duration_seconds: float = Field(default=8.0, ge=1.0, le=30.0)
    target_shot_count: int | None = Field(default=None, ge=1, le=2000)
    max_dialogue_lines_per_shot: int | None = Field(default=None, ge=0, le=30)
    directing_style: str = Field(
        default="cinematic, readable, emotionally motivated, and animation-efficient",
        min_length=3,
        max_length=500,
    )
    constraints: list[str] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def validate_duration_range(self) -> Self:
        if self.min_shot_duration_seconds > self.max_shot_duration_seconds:
            raise ValueError("Minimum shot duration cannot exceed maximum shot duration")
        return self


class ShotPlan(BaseModel):
    number: int = Field(ge=1)
    scene_number: int = Field(ge=1)
    duration_seconds: float = Field(ge=0.5, le=60)
    shot_size: str = Field(min_length=2, max_length=100)
    camera_angle: str = Field(min_length=2, max_length=200)
    camera_movement: str = Field(min_length=2, max_length=300)
    composition: str = Field(min_length=5, max_length=1000)
    location: str = Field(min_length=2, max_length=200)
    characters: list[str] = Field(default_factory=list, max_length=20)
    action: str = Field(min_length=3, max_length=1500)
    emotion: str = Field(min_length=2, max_length=300)
    dialogue_line_orders: list[int] = Field(default_factory=list, max_length=30)
    visual_prompt: str = Field(min_length=10, max_length=4000)
    animation_notes: list[str] = Field(default_factory=list, max_length=30)
    continuity_requirements: list[str] = Field(default_factory=list, max_length=30)
    transition: str = Field(default="cut", min_length=2, max_length=200)


class DirectedScene(BaseModel):
    scene_number: int = Field(ge=1)
    title: str = Field(min_length=2, max_length=200)
    estimated_duration_seconds: float = Field(ge=5, le=900)
    shots: list[ShotPlan] = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_shots(self) -> Self:
        numbers = [shot.number for shot in self.shots]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Shot numbers must start at 1 within each scene and remain sequential")
        if any(shot.scene_number != self.scene_number for shot in self.shots):
            raise ValueError("Every shot scene_number must match its directed scene")
        shot_total = sum(shot.duration_seconds for shot in self.shots)
        tolerance = max(2.0, self.estimated_duration_seconds * 0.1)
        if abs(shot_total - self.estimated_duration_seconds) > tolerance:
            raise ValueError("Shot durations must approximately match the directed scene duration")
        return self


class EpisodeDirection(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    aspect_ratio: str = Field(default="16:9", pattern=r"^\d{1,2}:\d{1,2}$")
    total_estimated_duration_seconds: float = Field(ge=30, le=4200)
    scenes: list[DirectedScene] = Field(min_length=3, max_length=60)
    global_visual_notes: list[str] = Field(default_factory=list, max_length=100)
    continuity_notes: list[str] = Field(default_factory=list, max_length=100)
    production_risks: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_episode_timing(self) -> Self:
        scene_numbers = [scene.scene_number for scene in self.scenes]
        if scene_numbers != list(range(1, len(scene_numbers) + 1)):
            raise ValueError("Directed scene numbers must start at 1 and remain sequential")
        scene_total = sum(scene.estimated_duration_seconds for scene in self.scenes)
        tolerance = max(10.0, self.total_estimated_duration_seconds * 0.1)
        if abs(scene_total - self.total_estimated_duration_seconds) > tolerance:
            raise ValueError("Directed scene durations must approximately match the episode duration")
        return self


class DirectionReviewRequest(BaseModel):
    decision: DirectionReviewStatus
    notes: str = Field(default="", max_length=4000)


class DirectionGenerationJobRead(BaseModel):
    id: str
    series_id: str
    script_job_id: str
    status: DirectionJobStatus
    review_status: DirectionReviewStatus = DirectionReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    model: str
    attempts: int
    request: DirectionGenerationRequest
    result: EpisodeDirection | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
