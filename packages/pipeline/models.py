from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ProductionStage(StrEnum):
    CONCEPT = "concept"
    STORY = "story"
    SCRIPT = "script"
    DIRECTION = "direction"
    VISUALS = "visuals"
    ANIMATION = "animation"
    VOICE = "voice"
    LIP_SYNC = "lip_sync"
    SOUND = "sound"
    QUALITY_CONTROL = "quality_control"
    RENDER = "render"
    APPROVAL = "approval"


class WorkflowStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    FAILED = "failed"


class EpisodeRequest(BaseModel):
    series_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=200)
    premise: str = Field(min_length=10)
    target_duration_seconds: int = Field(default=240, ge=60, le=3600)


class EpisodeState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    series_id: str
    title: str
    premise: str
    target_duration_seconds: int
    stage: ProductionStage = ProductionStage.CONCEPT
    status: WorkflowStatus = WorkflowStatus.PENDING_REVIEW
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
