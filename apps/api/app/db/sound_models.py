from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models import utc_now


class SoundMixJobRecord(Base):
    __tablename__ = "sound_mix_jobs"
    __table_args__ = (
        UniqueConstraint(
            "direction_job_id",
            "sound_key",
            name="uq_sound_mix_direction_key",
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
    source_job_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_job_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sound_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="planned", index=True
    )
    review_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending_review", index=True
    )
    review_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spec_payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    assets_payload: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
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
