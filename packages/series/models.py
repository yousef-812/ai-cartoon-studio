from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SeriesStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class VisualStyle(BaseModel):
    art_direction: str = Field(min_length=3, max_length=1000)
    medium: str = Field(default="2d animation", min_length=2, max_length=100)
    palette: list[str] = Field(default_factory=list, max_length=20)
    line_style: str = Field(default="clean", max_length=200)
    lighting: str = Field(default="cinematic", max_length=200)
    aspect_ratio: str = Field(default="16:9", pattern=r"^\d{1,2}:\d{1,2}$")


class SeriesRules(BaseModel):
    world_rules: list[str] = Field(default_factory=list, max_length=100)
    prohibited_topics: list[str] = Field(default_factory=list, max_length=100)
    continuity_notes: list[str] = Field(default_factory=list, max_length=100)


class SeriesCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    logline: str = Field(min_length=10, max_length=500)
    synopsis: str = Field(default="", max_length=5000)
    genre: str = Field(min_length=2, max_length=100)
    target_audience: str = Field(min_length=2, max_length=100)
    primary_language: str = Field(default="en", min_length=2, max_length=20)
    status: SeriesStatus = SeriesStatus.DRAFT
    visual_style: VisualStyle
    rules: SeriesRules = Field(default_factory=SeriesRules)


class SeriesUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=220)
    logline: str | None = Field(default=None, min_length=10, max_length=500)
    synopsis: str | None = Field(default=None, max_length=5000)
    genre: str | None = Field(default=None, min_length=2, max_length=100)
    target_audience: str | None = Field(default=None, min_length=2, max_length=100)
    primary_language: str | None = Field(default=None, min_length=2, max_length=20)
    status: SeriesStatus | None = None
    visual_style: VisualStyle | None = None
    rules: SeriesRules | None = None


class SeriesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    slug: str
    logline: str
    synopsis: str
    genre: str
    target_audience: str
    primary_language: str
    status: SeriesStatus
    visual_style: VisualStyle
    rules: SeriesRules
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=3000)
    visual_prompt: str = Field(min_length=10, max_length=3000)
    rules: list[str] = Field(default_factory=list, max_length=50)


class LocationRead(LocationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    series_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
