from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from packages.videos.models import GeneratedVideo


class LipSyncJobStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class LipSyncReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class LipSyncProviderHealth(BaseModel):
    available: bool
    provider: str
    detail: str = ""


class LipSyncPlanRequest(BaseModel):
    lead_in_ms: int = Field(default=250, ge=0, le=5000)
    tail_padding_ms: int = Field(default=250, ge=0, le=5000)
    minimum_gap_ms: int = Field(default=120, ge=0, le=5000)
    model: str = Field(default="", max_length=300)
    quality: str = Field(default="production", min_length=2, max_length=100)
    face_detection_confidence: float = Field(default=0.7, ge=0, le=1)
    preserve_original_audio: bool = False
    constraints: list[str] = Field(default_factory=list, max_length=50)


class DialoguePlacementSegment(BaseModel):
    voice_job_id: str = Field(min_length=1, max_length=100)
    dialogue_order: int = Field(ge=1)
    character_id: str = Field(min_length=1, max_length=100)
    character_name: str = Field(min_length=2, max_length=200)
    audio_path: str = Field(min_length=1, max_length=2000)
    start_time_seconds: float = Field(ge=0, le=3600)
    end_time_seconds: float = Field(gt=0, le=3600)
    pause_after_ms: int = Field(default=200, ge=0, le=5000)
    face_hint: str = Field(default="", max_length=1000)
    text: str = Field(default="", max_length=3000)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("Dialogue placement end must be after its start")
        return self


class LipSyncGenerationSpec(BaseModel):
    input_video_path: str = Field(min_length=1, max_length=2000)
    scene_number: int = Field(ge=1)
    shot_number: int = Field(ge=1)
    duration_seconds: float = Field(ge=0.5, le=300)
    segments: list[DialoguePlacementSegment] = Field(min_length=1, max_length=50)
    model: str = Field(default="", max_length=300)
    quality: str = Field(default="production", min_length=2, max_length=100)
    face_detection_confidence: float = Field(default=0.7, ge=0, le=1)
    preserve_original_audio: bool = False
    constraints: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_timeline(self) -> Self:
        previous_end = 0.0
        for segment in self.segments:
            if segment.start_time_seconds < previous_end:
                raise ValueError("Dialogue placement segments cannot overlap")
            if segment.end_time_seconds > self.duration_seconds:
                raise ValueError("Dialogue placement exceeds animated shot duration")
            previous_end = segment.end_time_seconds
        return self


class LipSyncShotSpec(BaseModel):
    key: str = Field(min_length=5, max_length=500)
    animation_job_id: str = Field(min_length=1, max_length=100)
    generation: LipSyncGenerationSpec


class RenderedLipSyncVideo(BaseModel):
    content: bytes = Field(repr=False)
    filename: str
    mime_type: str = "video/mp4"
    duration_seconds: float | None = Field(default=None, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)


class LipSyncReviewRequest(BaseModel):
    decision: LipSyncReviewStatus
    notes: str = Field(default="", max_length=4000)


class LipSyncJobRead(BaseModel):
    id: str
    series_id: str
    direction_job_id: str
    animation_job_id: str
    status: LipSyncJobStatus
    review_status: LipSyncReviewStatus = LipSyncReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    attempts: int
    spec: LipSyncShotSpec
    videos: list[GeneratedVideo] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
