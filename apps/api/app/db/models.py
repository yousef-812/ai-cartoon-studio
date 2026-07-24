from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class SeriesRecord(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    logline: Mapped[str] = mapped_column(String(500), nullable=False)
    synopsis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    visual_style: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    rules: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    characters: Mapped[list["CharacterRecord"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    locations: Mapped[list["LocationRecord"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    story_jobs: Mapped[list["StoryGenerationJobRecord"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    script_jobs: Mapped[list["ScriptGenerationJobRecord"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )
    direction_jobs: Mapped[list["DirectionGenerationJobRecord"]] = relationship(
        back_populates="series", cascade="all, delete-orphan"
    )


class CharacterRecord(Base):
    __tablename__ = "characters"
    __table_args__ = (UniqueConstraint("series_id", "name", name="uq_character_series_name"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    age_range: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    personality_traits: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    visual_identity: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    wardrobe: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    speaking_style: Mapped[str] = mapped_column(Text, nullable=False, default="")
    voice_profile: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    series: Mapped[SeriesRecord] = relationship(back_populates="characters")


class LocationRecord(Base):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint("series_id", "name", name="uq_location_series_name"),)

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    visual_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    rules: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    series: Mapped[SeriesRecord] = relationship(back_populates="locations")


class StoryGenerationJobRecord(Base):
    __tablename__ = "story_generation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(300), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    series: Mapped[SeriesRecord] = relationship(back_populates="story_jobs")
    script_jobs: Mapped[list["ScriptGenerationJobRecord"]] = relationship(
        back_populates="story_job", cascade="all, delete-orphan"
    )


class ScriptGenerationJobRecord(Base):
    __tablename__ = "script_generation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    story_job_id: Mapped[str] = mapped_column(
        ForeignKey("story_generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(300), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    series: Mapped[SeriesRecord] = relationship(back_populates="script_jobs")
    story_job: Mapped[StoryGenerationJobRecord] = relationship(back_populates="script_jobs")
    direction_jobs: Mapped[list["DirectionGenerationJobRecord"]] = relationship(
        back_populates="script_job", cascade="all, delete-orphan"
    )


class DirectionGenerationJobRecord(Base):
    __tablename__ = "direction_generation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_job_id: Mapped[str] = mapped_column(
        ForeignKey("script_generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(300), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    result_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    series: Mapped[SeriesRecord] = relationship(back_populates="direction_jobs")
    script_job: Mapped[ScriptGenerationJobRecord] = relationship(back_populates="direction_jobs")
