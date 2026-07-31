from pydantic import BaseModel, Field


class ImageProviderHealth(BaseModel):
    available: bool
    provider: str
    detail: str = ""


class ImageGenerationSpec(BaseModel):
    prompt: str = Field(min_length=10, max_length=8000)
    negative_prompt: str = Field(default="", max_length=4000)
    width: int = Field(default=1280, ge=256, le=4096)
    height: int = Field(default=720, ge=256, le=4096)
    seed: int = Field(default=-1, ge=-1)
    steps: int = Field(default=28, ge=1, le=150)
    guidance_scale: float = Field(default=6.5, ge=0, le=30)
    reference_urls: list[str] = Field(default_factory=list, max_length=20)
    metadata: dict[str, object] = Field(default_factory=dict)


class ImageProviderSubmission(BaseModel):
    provider_job_id: str


class GeneratedImage(BaseModel):
    url: str
    filename: str = ""
    storage_path: str = ""
    checksum_sha256: str = ""
    mime_type: str = "image/png"
    size_bytes: int | None = None
    width: int | None = None
    height: int | None = None
    seed: int | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class ImageProviderResult(BaseModel):
    completed: bool
    images: list[GeneratedImage] = Field(default_factory=list)
    detail: str = ""
