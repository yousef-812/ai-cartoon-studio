import asyncio
import hashlib

import httpx

from packages.artifacts.local_store import LocalArtifactStore
from packages.videos.models import GeneratedVideo, VideoProviderResult


def test_local_artifact_store_persists_video_with_checksum(tmp_path) -> None:
    content = b"fake-mp4-content"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "video.example"
        return httpx.Response(200, content=content, headers={"content-type": "video/mp4"})

    store = LocalArtifactStore(
        str(tmp_path),
        allowed_base_url="https://video.example",
        transport=httpx.MockTransport(handler),
    )
    result = VideoProviderResult(
        completed=True,
        videos=[
            GeneratedVideo(
                url="https://video.example/view?filename=shot.mp4",
                filename="shot.mp4",
            )
        ],
    )

    persisted = asyncio.run(
        store.persist_video_result(
            result,
            series_id="series-1",
            animation_id="animation-1",
        )
    )

    video = persisted.videos[0]
    assert video.size_bytes == len(content)
    assert video.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert video.storage_path.endswith("series-1/animated-shots/animation-1/01.mp4")
    assert (tmp_path / "series-1" / "animated-shots" / "animation-1" / "01.mp4").read_bytes() == content
