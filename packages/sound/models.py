from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from packages.videos.models import GeneratedVideo


class SoundCueKind(StrEnum):
    AMBIENCE = "ambience"
    EFFECT = "effect"
    MUSIC = "music"


class SoundMixJobStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SoundMixReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class SoundProviderHealth(BaseModel):
    available: bool
    provider: str
    detail: str = ""


class SoundSystemHealth(BaseModel):
    available: bool
    provider: SoundProviderHealth
    ffmpeg_available: bool
    detail: str = ""


class SoundPlanRequest(BaseModel):
    include_ambience: bool = True
    include_effects: bool = True
    include_music: bool = True
    ambience_gain_db: float = Field(default=-20.0, ge=-60, le=6)
    effects_gain_db: float = Field(default=-12.0, ge=-60, le=6)
    music_gain_db: float = Field(default=-22.0, ge=-60, le=6)
    dialogue_ducking_db: float = Field(default=-10.0, ge=-40, le=0)
    target_loudness_lufs: float = Field(default=-16.0, ge=-24, le=-5)
    sound_model: str = Field(default="", max_length=300)
    music_model: str = Field(default="", max_length=300)
    constraints: list[str] = Field(default_factory=list, max_length=50)


class SoundCueSpec(BaseModel):
    key: str = Field(min_length=5, max_length=500)
    kind: SoundCueKind
    prompt: str = Field(min_length=5, max_length=3000)
    start_time_seconds: float = Field(default=0, ge=0, le=3600)
    duration_seconds: float = Field(ge=0.1, le=600)
    gain_db: float = Field(default=-18.0, ge=-60, le=12)
    loop: bool = False
    fade_in_seconds: float = Field(default=0.05, ge=0, le=30)
    fade_out_seconds: float = Field(default=0.1, ge=0, le=30)
    model: str = Field(default="", max_length=300)
    seed: int | None = Field(default=None, ge=0, le=2**31 - 1)
    metadata: dict[str, object] = Field(default_factory=dict)


class DialogueDuckingWindow(BaseModel):
    start_time_seconds: float = Field(ge=0, le=3600)
    end_time_seconds: float = Field(gt=0, le=3600)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("Dialogue ducking window end must be after its start")
        return self


class SoundMixGenerationSpec(BaseModel):
    input_video_path: str = Field(min_length=1, max_length=2000)
    source_has_dialogue: bool = False
    scene_number: int = Field(ge=1)
    shot_number: int = Field(ge=1)
    duration_seconds: float = Field(ge=0.5, le=600)
    cues: list[SoundCueSpec] = Field(min_length=1, max_length=100)
    dialogue_windows: list[DialogueDuckingWindow] = Field(default_factory=list, max_length=100)
    dialogue_ducking_db: float = Field(default=-10.0, ge=-40, le=0)
    target_loudness_lufs: float = Field(default=-16.0, ge=-24, le=-5)
    output_format: str = Field(default="mp4", pattern=r"^(mp4|mov|mkv)$")
    constraints: list[str] = Field(default_factory=list, max_length=50)
    metadata: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_timeline(self) -> Self:
        for cue in self.cues:
            if cue.start_time_seconds + cue.duration_seconds > self.duration_seconds + 0.05:
                raise ValueError("Sound cue exceeds shot duration")
        previous_end = 0.0
        for window in self.dialogue_windows:
            if window.start_time_seconds < previous_end:
                raise ValueError("Dialogue ducking windows cannot overlap")
            if window.end_time_seconds > self.duration_seconds:
                raise ValueError("Dialogue ducking window exceeds shot duration")
            previous_end = window.end_time_seconds
        return self


class SoundMixJobSpec(BaseModel):
    key: str = Field(min_length=5, max_length=500)
    source_job_type: str = Field(pattern=r"^(animation|lip_sync)$")
    source_job_id: str = Field(min_length=1, max_length=100)
    generation: SoundMixGenerationSpec


class RenderedSoundAsset(BaseModel):
    content: bytes = Field(repr=False)
    filename: str
    mime_type: str = "audio/wav"
    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class GeneratedSoundAsset(BaseModel):
    id: str = ""
    cue_key: str
    kind: SoundCueKind
    prompt: str
    url: str = ""
    filename: str = ""
    storage_path: str = ""
    mime_type: str = "audio/wav"
    size_bytes: int | None = Field(default=None, ge=0)
    checksum_sha256: str = ""
    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class RenderedSoundMix(BaseModel):
    content: bytes = Field(repr=False)
    filename: str
    mime_type: str = "video/mp4"
    duration_seconds: float | None = Field(default=None, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)


class SoundMixReviewRequest(BaseModel):
    decision: SoundMixReviewStatus
    notes: str = Field(default="", max_length=4000)


class SoundMixJobRead(BaseModel):
    id: str
    series_id: str
    direction_job_id: str
    source_job_type: str
    source_job_id: str
    status: SoundMixJobStatus
    review_status: SoundMixReviewStatus = SoundMixReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    provider: str
    attempts: int
    spec: SoundMixJobSpec
    assets: list[GeneratedSoundAsset] = Field(default_factory=list)
    videos: list[GeneratedVideo] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
