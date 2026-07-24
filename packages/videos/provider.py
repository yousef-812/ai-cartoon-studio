from typing import Protocol

from packages.videos.models import (
    VideoGenerationSpec,
    VideoProviderHealth,
    VideoProviderResult,
    VideoProviderSubmission,
)


class VideoProvider(Protocol):
    name: str

    async def health(self) -> VideoProviderHealth: ...

    async def submit(self, spec: VideoGenerationSpec) -> VideoProviderSubmission: ...

    async def result(self, provider_job_id: str) -> VideoProviderResult: ...

    async def wait_for_result(self, provider_job_id: str) -> VideoProviderResult: ...
