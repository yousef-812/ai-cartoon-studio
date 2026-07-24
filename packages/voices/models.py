from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from packages.audio.models import GeneratedAudio, SpeechSynthesisSpec


class VoiceJobStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class VoiceReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class VoicePlanRequest(BaseModel):
    response_format: str = Field(default="wav", pattern=r"^(wav|mp3|flac|opus)$")
    model: str = Field(default="", max_length=300)
    global_speed_multiplier: float = Field(default=1.0, ge=0.5, le=2.0)
    constraints: list[str] = Field(default_factory=list, max_length=50)


class VoiceLineSpec(BaseModel):
    key: str = Field(min_length=5, max_length=500)
    scene_number: int = Field(ge=1)
    dialogue_order: int = Field(ge=1)
    character_id: str = Field(min_length=1, max_length=100)
    character_name: str = Field(min_length=2, max_length=200)
    pause_after_ms: int = Field(default=200, ge=0, le=5000)
    synthesis: SpeechSynthesisSpec


class VoiceReviewRequest(BaseModel):
    decision: VoiceReviewStatus
    notes: str = Field(default="", max_length=4000)


class VoiceJobRead(BaseModel):
    id: str
    series_id: str
    script_job_id: str
    character_id: str
    status: VoiceJobStatus
    review_status: VoiceReviewStatus = VoiceReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    attempts: int
    spec: VoiceLineSpec
    audio: GeneratedAudio | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
