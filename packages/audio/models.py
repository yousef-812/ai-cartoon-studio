from pydantic import BaseModel, Field


class AudioProviderHealth(BaseModel):
    available: bool
    provider: str
    model: str = ""
    detail: str = ""


class SpeechSynthesisSpec(BaseModel):
    text: str = Field(min_length=1, max_length=3000)
    voice_id: str = Field(min_length=1, max_length=300)
    model: str = Field(default="", max_length=300)
    language: str = Field(default="en", min_length=2, max_length=40)
    emotion: str = Field(default="neutral", min_length=2, max_length=200)
    delivery: str = Field(default="natural", min_length=2, max_length=300)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    response_format: str = Field(default="wav", pattern=r"^(wav|mp3|flac|opus)$")
    target_duration_seconds: float | None = Field(default=None, ge=0.2, le=60)
    metadata: dict[str, object] = Field(default_factory=dict)


class SynthesizedAudio(BaseModel):
    content: bytes = Field(repr=False)
    filename: str
    mime_type: str
    duration_seconds: float | None = Field(default=None, ge=0)
    sample_rate: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)
    metadata: dict[str, object] = Field(default_factory=dict)


class GeneratedAudio(BaseModel):
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
