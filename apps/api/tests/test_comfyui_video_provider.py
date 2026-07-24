import asyncio
import json

import httpx

from packages.videos.comfyui import ComfyUIVideoProvider
from packages.videos.models import VideoGenerationSpec


def test_comfyui_video_provider_uploads_keyframe_and_extracts_mp4(tmp_path) -> None:
    image_path = tmp_path / "keyframe.png"
    image_path.write_bytes(b"fake-image")
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "workflow": {
                    "1": {"inputs": {"image": "placeholder.png"}},
                    "3": {"inputs": {"video_frames": 1, "fps": 1}},
                    "5": {"inputs": {"seed": 1}},
                },
                "bindings": {
                    "input_image": {"node_id": "1", "input_name": "image"},
                    "frames": {"node_id": "3", "input_name": "video_frames"},
                    "fps": {"node_id": "3", "input_name": "fps"},
                    "seed": {"node_id": "5", "input_name": "seed"},
                },
            }
        ),
        encoding="utf-8",
    )
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/upload/image":
            return httpx.Response(200, json={"name": "keyframe.png", "subfolder": "studio"})
        if request.url.path == "/prompt":
            body = json.loads(request.content)
            observed["workflow"] = body["prompt"]
            return httpx.Response(200, json={"prompt_id": "video-job-1"})
        if request.url.path == "/history/video-job-1":
            return httpx.Response(
                200,
                json={
                    "video-job-1": {
                        "outputs": {
                            "7": {
                                "gifs": [
                                    {
                                        "filename": "shot.mp4",
                                        "subfolder": "clips",
                                        "type": "output",
                                    }
                                ]
                            }
                        },
                        "status": {"completed": True},
                    }
                },
            )
        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    provider = ComfyUIVideoProvider(
        base_url="https://video.example",
        workflow_path=str(workflow_path),
        transport=httpx.MockTransport(handler),
    )
    spec = VideoGenerationSpec(
        input_image_path=str(image_path),
        prompt="Animate the character taking one careful step forward.",
        duration_seconds=2,
        fps=8,
        seed=42,
    )

    submission = asyncio.run(provider.submit(spec))
    result = asyncio.run(provider.result(submission.provider_job_id))

    workflow = observed["workflow"]
    assert isinstance(workflow, dict)
    assert workflow["1"]["inputs"]["image"] == "studio/keyframe.png"
    assert workflow["3"]["inputs"]["video_frames"] == 16
    assert workflow["3"]["inputs"]["fps"] == 8
    assert workflow["5"]["inputs"]["seed"] == 42
    assert result.completed is True
    assert result.videos[0].filename == "shot.mp4"
    assert "filename=shot.mp4" in result.videos[0].url
