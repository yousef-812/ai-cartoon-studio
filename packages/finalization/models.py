from datetime import UTC, datetime
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class FinalizationJobStatus(StrEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class FinalizationReviewStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"


class QCSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class QCCheck(BaseModel):
    code: str = Field(min_length=2, max_length=100)
    severity: QCSeverity
    passed: bool
    message: str = Field(min_length=2, max_length=2000)
    scene_number: int | None = Field(default=None, ge=1)
    shot_number: int | None = Field(default=None, ge=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class QCReport(BaseModel):
    passed: bool
    checks: list[QCCheck] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def errors(self) -> list[QCCheck]:
        return [check for check in self.checks if not check.passed and check.severity == QCSeverity.ERROR]


class SubtitleCue(BaseModel):
    index: int = Field(ge=1)
    start_time_seconds: float = Field(ge=0, le=14400)
    end_time_seconds: float = Field(gt=0, le=14400)
    text: str = Field(min_length=1, max_length=4000)
    speaker: str = Field(default="", max_length=200)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end_time_seconds <= self.start_time_seconds:
            raise ValueError("Subtitle cue end must be after its start")
        return self


class FinalShotSpec(BaseModel):
    sound_job_id: str = Field(min_length=1, max_length=100)
    scene_number: int = Field(ge=1)
    shot_number: int = Field(ge=1)
    input_video_path: str = Field(min_length=1, max_length=2000)
    duration_seconds: float = Field(ge=0.5, le=600)
    timeline_start_seconds: float = Field(ge=0, le=14400)
    timeline_end_seconds: float = Field(gt=0, le=14400)
    transition: str = Field(default="cut", max_length=200)

    @model_validator(mode="after")
    def validate_timeline(self) -> Self:
        if self.timeline_end_seconds <= self.timeline_start_seconds:
            raise ValueError("Final shot timeline end must be after its start")
        expected = self.timeline_end_seconds - self.timeline_start_seconds
        if abs(expected - self.duration_seconds) > 0.05:
            raise ValueError("Final shot duration must match its timeline range")
        return self


class ShortCandidateSpec(BaseModel):
    index: int = Field(ge=1)
    start_time_seconds: float = Field(ge=0, le=14400)
    duration_seconds: float = Field(ge=5, le=180)
    title: str = Field(min_length=2, max_length=200)
    scene_number: int = Field(ge=1)


class FinalizationPlanRequest(BaseModel):
    include_subtitles: bool = True
    burn_subtitles: bool = False
    subtitle_language: str = Field(default="en", min_length=2, max_length=20)
    generate_thumbnail: bool = True
    shorts_candidate_count: int = Field(default=3, ge=0, le=6)
    shorts_duration_seconds: float = Field(default=30.0, ge=10, le=60)
    output_width: int = Field(default=1920, ge=640, le=3840)
    output_height: int = Field(default=1080, ge=360, le=2160)
    output_fps: int = Field(default=24, ge=12, le=60)
    video_codec: str = Field(default="libx264", min_length=2, max_length=100)
    audio_codec: str = Field(default="aac", min_length=2, max_length=100)
    target_loudness_lufs: float = Field(default=-16.0, ge=-24, le=-5)
    silence_threshold_db: float = Field(default=-45.0, ge=-80, le=-20)
    max_silence_seconds: float = Field(default=2.0, ge=0.2, le=15)
    max_peak_db: float = Field(default=-1.0, ge=-12, le=0)


class FinalizationJobSpec(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    direction_job_id: str = Field(min_length=1, max_length=100)
    shots: list[FinalShotSpec] = Field(min_length=1, max_length=2000)
    subtitles: list[SubtitleCue] = Field(default_factory=list, max_length=5000)
    short_candidates: list[ShortCandidateSpec] = Field(default_factory=list, max_length=6)
    total_duration_seconds: float = Field(ge=1, le=14400)
    request: FinalizationPlanRequest
    preflight_report: QCReport

    @model_validator(mode="after")
    def validate_shots(self) -> Self:
        previous_end = 0.0
        for shot in self.shots:
            if abs(shot.timeline_start_seconds - previous_end) > 0.05:
                raise ValueError("Final shots must form one continuous timeline")
            previous_end = shot.timeline_end_seconds
        if abs(previous_end - self.total_duration_seconds) > 0.05:
            raise ValueError("Final timeline must match total duration")
        return self


class FinalArtifact(BaseModel):
    kind: str = Field(min_length=2, max_length=100)
    url: str = ""
    filename: str = ""
    storage_path: str = ""
    mime_type: str = "application/octet-stream"
    size_bytes: int | None = Field(default=None, ge=0)
    checksum_sha256: str = ""
    duration_seconds: float | None = Field(default=None, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)


class FinalizationReviewRequest(BaseModel):
    decision: FinalizationReviewStatus
    notes: str = Field(default="", max_length=4000)


class FinalizationJobRead(BaseModel):
    id: str
    series_id: str
    direction_job_id: str
    status: FinalizationJobStatus
    review_status: FinalizationReviewStatus = FinalizationReviewStatus.PENDING_REVIEW
    review_notes: str = ""
    attempts: int
    spec: FinalizationJobSpec
    report: QCReport | None = None
    artifacts: list[FinalArtifact] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    reviewed_at: datetime | None = None
