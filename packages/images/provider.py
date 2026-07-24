from typing import Protocol

from packages.images.models import (
    ImageGenerationSpec,
    ImageProviderHealth,
    ImageProviderResult,
    ImageProviderSubmission,
)


class ImageProvider(Protocol):
    name: str

    async def health(self) -> ImageProviderHealth: ...

    async def submit(self, spec: ImageGenerationSpec) -> ImageProviderSubmission: ...

    async def result(self, provider_job_id: str) -> ImageProviderResult: ...
