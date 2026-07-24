from pydantic import BaseModel, Field, model_validator
from typing import Self


class VideoProviderHealth(BaseModel):
    available: bool
    provider: str
    detail: str = ""


class VideoGenerationSpec(BaseModel):
    input_image_path: str = Field(min_length=1, max_length=2000)
    prompt: str = Field(min_length=10, max_length=8000)
    negative_prompt: str = Field(default="", max_length=4000)
    width: int = Field(default=1280, ge=256, le=4096)
    height: int = Field(default=720, ge=256, le=4096)
    duration_seconds: float = Field(default=4.0, ge=0.5, le=30.0)
    fps: int = Field(default=16, ge=4, le=60)
    seed: int = Field(default=-1, ge=-1)
    steps: int = Field(default=25, ge=1, le=150)
    guidance_scale: float = Field(default=3.0, ge=0, le=30)
    motion_strength: float = Field(default=0.55, ge=0, le=1)
    metadata: dict[str, object] = Field(default_factory=dict)

    @property
    def frame_count(self) -> int:
        return max(1, round(self.duration_seconds * self.fps))

    @model_validator(mode="after")
    def validate_frame_budget(self) -> Self:
        if self.frame_count > 600:
            raise ValueError("A single animated shot cannot exceed 600 frames")
        return self


class VideoProviderSubmission(BaseModel):
    provider_job_id: str


class GeneratedVideo(BaseModel):
    url: str = ""
    filename: str = ""
    storage_path: str = ""
    mime_type: str = "video/mp4"
    size_bytes: int | None = Field(default=None, ge=0)
    checksum_sha256: str = ""
    duration_seconds: float | None = Field(default=None, ge=0)
    fps: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class VideoProviderResult(BaseModel):
    completed: bool
    videos: list[GeneratedVideo] = Field(default_factory=list)
    detail: str = ""
