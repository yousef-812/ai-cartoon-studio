from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from packages.videos.models import GeneratedVideo, VideoGenerationSpec


class AnimationJobStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class AnimationReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class AnimationEngine(StrEnum):
    IMAGE_TO_VIDEO = "image_to_video"
    BLENDER = "blender"


class AnimationPlanRequest(BaseModel):
    engine: AnimationEngine = AnimationEngine.IMAGE_TO_VIDEO
    fps: int = Field(default=16, ge=4, le=60)
    max_clip_duration_seconds: float = Field(default=12.0, ge=1.0, le=30.0)
    motion_strength: float = Field(default=0.55, ge=0, le=1)
    steps: int = Field(default=25, ge=1, le=150)
    guidance_scale: float = Field(default=3.0, ge=0, le=30)
    constraints: list[str] = Field(default_factory=list, max_length=50)
    blender_scene_path: str = Field(default="", max_length=2000)
    blender_registry_path: str = Field(default="", max_length=2000)
    blender_render_engine: str = Field(default="BLENDER_EEVEE_NEXT", max_length=100)
    blender_samples: int = Field(default=32, ge=1, le=4096)
    width: int = Field(default=1280, ge=256, le=4096)
    height: int = Field(default=720, ge=256, le=4096)

    @model_validator(mode="after")
    def validate_engine_configuration(self) -> Self:
        if self.engine == AnimationEngine.BLENDER:
            if not self.blender_scene_path:
                raise ValueError("blender_scene_path is required for Blender animation")
            if not self.blender_registry_path:
                raise ValueError("blender_registry_path is required for Blender animation")
        return self


class AnimatedShotSpec(BaseModel):
    key: str = Field(min_length=5, max_length=500)
    scene_number: int = Field(ge=1)
    shot_number: int = Field(ge=1)
    keyframe_asset_id: str = Field(min_length=1, max_length=100)
    generation: VideoGenerationSpec


class AnimationReviewRequest(BaseModel):
    decision: AnimationReviewStatus
    notes: str = Field(default="", max_length=4000)


class AnimationJobRead(BaseModel):
    id: str
    series_id: str
    direction_job_id: str
    keyframe_asset_id: str
    status: AnimationJobStatus
    review_status: AnimationReviewStatus = AnimationReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    attempts: int
    provider_job_id: str | None = None
    spec: AnimatedShotSpec
    videos: list[GeneratedVideo] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
