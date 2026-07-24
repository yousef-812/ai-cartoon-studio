import asyncio
import hashlib

import httpx

from packages.artifacts.local_store import LocalArtifactStore
from packages.images.models import GeneratedImage, ImageProviderResult


def test_local_artifact_store_downloads_and_hashes_provider_image(tmp_path) -> None:
    content = b"fake-png-content"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "comfy.test"
        return httpx.Response(200, content=content, headers={"content-type": "image/png"})

    store = LocalArtifactStore(
        str(tmp_path),
        allowed_base_url="http://comfy.test",
        transport=httpx.MockTransport(handler),
    )
    result = asyncio.run(
        store.persist_result(
            ImageProviderResult(
                completed=True,
                images=[
                    GeneratedImage(
                        url="http://comfy.test/view?filename=shot.png",
                        filename="shot.png",
                    )
                ],
            ),
            series_id="series-1",
            asset_id="asset-1",
        )
    )

    image = result.images[0]
    assert image.storage_path
    assert image.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert image.size_bytes == len(content)
    assert image.mime_type == "image/png"
    assert open(image.storage_path, "rb").read() == content
