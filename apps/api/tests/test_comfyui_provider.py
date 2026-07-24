import asyncio
import json

import httpx

from packages.images.comfyui import ComfyUIImageProvider
from packages.images.models import ImageGenerationSpec


def test_comfyui_provider_injects_workflow_and_reads_images(tmp_path) -> None:
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "workflow": {
                    "1": {"class_type": "CLIPTextEncode", "inputs": {"text": "old"}},
                    "2": {"class_type": "EmptyLatentImage", "inputs": {"width": 512, "height": 512}},
                },
                "bindings": {
                    "prompt": {"node_id": "1", "input_name": "text"},
                    "width": {"node_id": "2", "input_name": "width"},
                    "height": {"node_id": "2", "input_name": "height"},
                },
            }
        ),
        encoding="utf-8",
    )
    submitted: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/system_stats":
            return httpx.Response(200, json={"devices": []})
        if request.url.path == "/prompt":
            submitted.update(json.loads(request.content))
            return httpx.Response(200, json={"prompt_id": "visual-123"})
        if request.url.path == "/history/visual-123":
            return httpx.Response(
                200,
                json={
                    "visual-123": {
                        "status": {"completed": True},
                        "outputs": {
                            "9": {
                                "images": [
                                    {
                                        "filename": "shot.png",
                                        "subfolder": "episode-1",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                    }
                },
            )
        return httpx.Response(404)

    provider = ComfyUIImageProvider(
        base_url="http://comfy.test",
        workflow_path=str(workflow_path),
        transport=httpx.MockTransport(handler),
        poll_interval_seconds=0.01,
    )

    health = asyncio.run(provider.health())
    submission = asyncio.run(
        provider.submit(
            ImageGenerationSpec(
                prompt="Mira in a cinematic cloud engine room.",
                width=1280,
                height=720,
            )
        )
    )
    result = asyncio.run(provider.result(submission.provider_job_id))

    workflow = submitted["prompt"]
    assert isinstance(workflow, dict)
    assert workflow["1"]["inputs"]["text"] == "Mira in a cinematic cloud engine room."
    assert workflow["2"]["inputs"]["width"] == 1280
    assert workflow["2"]["inputs"]["height"] == 720
    assert health.available is True
    assert result.completed is True
    assert result.images[0].filename == "shot.png"
    assert "episode-1" in result.images[0].url
