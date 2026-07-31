from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from packages.images.models import GeneratedImage, ImageGenerationSpec


class VisualAssetType(StrEnum):
    CHARACTER_REFERENCE = "character_reference"
    CHARACTER_EXPRESSION_SHEET = "character_expression_sheet"
    CHARACTER_POSE_SHEET = "character_pose_sheet"
    BACKGROUND = "background"
    PROP = "prop"
    SHOT_KEYFRAME = "shot_keyframe"


class VisualAssetStatus(StrEnum):
    PLANNED = "planned"
    BLOCKED = "blocked"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class VisualAssetReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class VisualAssetSpec(BaseModel):
    key: str = Field(min_length=3, max_length=500)
    asset_type: VisualAssetType
    name: str = Field(min_length=2, max_length=300)
    scene_number: int | None = Field(default=None, ge=1)
    shot_number: int | None = Field(default=None, ge=1)
    character_name: str | None = Field(default=None, max_length=200)
    location_name: str | None = Field(default=None, max_length=200)
    dependency_keys: list[str] = Field(default_factory=list, max_length=50)
    generation: ImageGenerationSpec


class VisualAssetReviewRequest(BaseModel):
    decision: VisualAssetReviewStatus
    notes: str = Field(default="", max_length=4000)


class VisualAssetRead(BaseModel):
    id: str
    series_id: str
    direction_job_id: str
    status: VisualAssetStatus
    review_status: VisualAssetReviewStatus = VisualAssetReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    attempts: int
    provider_job_id: str | None = None
    spec: VisualAssetSpec
    images: list[GeneratedImage] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
