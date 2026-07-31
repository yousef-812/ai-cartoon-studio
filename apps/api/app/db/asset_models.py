from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models import utc_now


class VisualAssetRecord(Base):
    __tablename__ = "visual_assets"
    __table_args__ = (
        UniqueConstraint(
            "direction_job_id",
            "asset_key",
            name="uq_visual_asset_direction_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction_job_id: Mapped[str] = mapped_column(
        ForeignKey("direction_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_key: Mapped[str] = mapped_column(String(500), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spec_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    images_payload: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
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


class AnimationJobRecord(Base):
    __tablename__ = "animation_jobs"
    __table_args__ = (
        UniqueConstraint(
            "direction_job_id",
            "animation_key",
            name="uq_animation_direction_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction_job_id: Mapped[str] = mapped_column(
        ForeignKey("direction_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    keyframe_asset_id: Mapped[str] = mapped_column(
        ForeignKey("visual_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    animation_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_job_id: Mapped[str | None] = mapped_column(String(300), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spec_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    videos_payload: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
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


class VoiceLineJobRecord(Base):
    __tablename__ = "voice_line_jobs"
    __table_args__ = (
        UniqueConstraint(
            "script_job_id",
            "voice_key",
            name="uq_voice_script_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    script_job_id: Mapped[str] = mapped_column(
        ForeignKey("script_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[str] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voice_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spec_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    audio_payload: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
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


class LipSyncJobRecord(Base):
    __tablename__ = "lip_sync_jobs"
    __table_args__ = (
        UniqueConstraint(
            "direction_job_id",
            "lip_sync_key",
            name="uq_lip_sync_direction_key",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    series_id: Mapped[str] = mapped_column(
        ForeignKey("series.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction_job_id: Mapped[str] = mapped_column(
        ForeignKey("direction_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    animation_job_id: Mapped[str] = mapped_column(
        ForeignKey("animation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lip_sync_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="planned", index=True)
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spec_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    videos_payload: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
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
