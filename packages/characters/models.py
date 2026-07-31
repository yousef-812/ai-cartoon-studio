from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class CharacterRole(StrEnum):
    PROTAGONIST = "protagonist"
    DEUTERAGONIST = "deuteragonist"
    SUPPORTING = "supporting"
    ANTAGONIST = "antagonist"
    RECURRING = "recurring"


class VisualIdentity(BaseModel):
    reference_prompt: str = Field(min_length=10, max_length=4000)
    body_shape: str = Field(default="", max_length=500)
    face: str = Field(default="", max_length=500)
    hair: str = Field(default="", max_length=500)
    palette: list[str] = Field(default_factory=list, max_length=20)
    signature_features: list[str] = Field(default_factory=list, max_length=30)


class VoiceProfile(BaseModel):
    provider: str = Field(default="", max_length=100)
    voice_id: str = Field(default="", max_length=200)
    language: str = Field(default="en", min_length=2, max_length=20)
    description: str = Field(default="", max_length=1000)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class CharacterCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    role: CharacterRole
    age_range: str = Field(default="", max_length=100)
    description: str = Field(min_length=10, max_length=3000)
    personality_traits: list[str] = Field(default_factory=list, max_length=30)
    visual_identity: VisualIdentity
    wardrobe: dict[str, str] = Field(default_factory=dict)
    speaking_style: str = Field(default="", max_length=1000)
    voice_profile: VoiceProfile = Field(default_factory=VoiceProfile)


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    role: CharacterRole | None = None
    age_range: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=3000)
    personality_traits: list[str] | None = Field(default=None, max_length=30)
    visual_identity: VisualIdentity | None = None
    wardrobe: dict[str, str] | None = None
    speaking_style: str | None = Field(default=None, max_length=1000)
    voice_profile: VoiceProfile | None = None


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    series_id: str
    name: str
    role: CharacterRole
    age_range: str
    description: str
    personality_traits: list[str]
    visual_identity: VisualIdentity
    wardrobe: dict[str, str]
    speaking_style: str
    voice_profile: VoiceProfile
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
