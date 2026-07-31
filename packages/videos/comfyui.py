import asyncio
import copy
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field

from packages.videos.errors import (
    VideoProviderResponseError,
    VideoProviderUnavailableError,
)
from packages.videos.models import (
    GeneratedVideo,
    VideoGenerationSpec,
    VideoProviderHealth,
    VideoProviderResult,
    VideoProviderSubmission,
)


class WorkflowBinding(BaseModel):
    node_id: str
    input_name: str


class ComfyUIVideoWorkflowTemplate(BaseModel):
    workflow: dict[str, Any]
    bindings: dict[str, WorkflowBinding] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "ComfyUIVideoWorkflowTemplate":
        if not path:
            raise VideoProviderUnavailableError("VIDEO_WORKFLOW_PATH is not configured")
        try:
            return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise VideoProviderUnavailableError(
                f"Could not load ComfyUI video workflow: {error}"
            ) from error

    def render(self, spec: VideoGenerationSpec, uploaded_image_name: str) -> dict[str, Any]:
        workflow = copy.deepcopy(self.workflow)
        values: dict[str, object] = {
            "input_image": uploaded_image_name,
            "prompt": spec.prompt,
            "negative_prompt": spec.negative_prompt,
            "width": spec.width,
            "height": spec.height,
            "frames": spec.frame_count,
            "fps": spec.fps,
            "seed": spec.seed,
            "steps": spec.steps,
            "guidance_scale": spec.guidance_scale,
            "motion_strength": spec.motion_strength,
        }
        for key, value in values.items():
            binding = self.bindings.get(key)
            if binding is None:
                continue
            try:
                workflow[binding.node_id]["inputs"][binding.input_name] = value
            except (KeyError, TypeError) as error:
                raise VideoProviderResponseError(
                    f"Invalid ComfyUI video binding for '{key}' at node {binding.node_id}"
                ) from error
        return workflow


class ComfyUIVideoProvider:
    name = "local-comfyui-video"

    def __init__(
        self,
        *,
        base_url: str,
        workflow_path: str,
        client_id: str = "ai-cartoon-studio-video",
        timeout_seconds: float = 900,
        poll_interval_seconds: float = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_path = workflow_path
        self.client_id = client_id
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.transport = transport

    async def health(self) -> VideoProviderHealth:
        if not self.base_url:
            return VideoProviderHealth(
                available=False,
                provider=self.name,
                detail="VIDEO_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                response.raise_for_status()
            ComfyUIVideoWorkflowTemplate.from_file(self.workflow_path)
            return VideoProviderHealth(
                available=True,
                provider=self.name,
                detail="Self-hosted ComfyUI video endpoint and workflow are ready.",
            )
        except (httpx.HTTPError, VideoProviderUnavailableError) as error:
            return VideoProviderHealth(
                available=False,
                provider=self.name,
                detail=str(error),
            )

    async def upload_input_image(self, image_path: str) -> str:
        path = Path(image_path).resolve()
        if not path.is_file():
            raise VideoProviderResponseError("Animation input image does not exist")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                with path.open("rb") as image_file:
                    response = await client.post(
                        f"{self.base_url}/upload/image",
                        files={"image": (path.name, image_file, "application/octet-stream")},
                        data={"type": "input", "overwrite": "true"},
                    )
                response.raise_for_status()
                body = response.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise VideoProviderUnavailableError(str(error)) from error
        except (httpx.HTTPError, OSError, ValueError) as error:
            raise VideoProviderResponseError(str(error)) from error

        name = body.get("name") if isinstance(body, dict) else None
        if not isinstance(name, str) or not name:
            raise VideoProviderResponseError("ComfyUI upload response did not contain an image name")
        subfolder = body.get("subfolder", "") if isinstance(body, dict) else ""
        return f"{subfolder}/{name}".strip("/")

    async def submit(self, spec: VideoGenerationSpec) -> VideoProviderSubmission:
        if not self.base_url:
            raise VideoProviderUnavailableError("VIDEO_BASE_URL is not configured")
        template = ComfyUIVideoWorkflowTemplate.from_file(self.workflow_path)
        uploaded_image_name = await self.upload_input_image(spec.input_image_path)
        payload = {
            "prompt": template.render(spec, uploaded_image_name),
            "client_id": self.client_id,
        }
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(f"{self.base_url}/prompt", json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise VideoProviderUnavailableError(str(error)) from error
        except httpx.HTTPError as error:
            raise VideoProviderResponseError(str(error)) from error
        prompt_id = body.get("prompt_id") if isinstance(body, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            raise VideoProviderResponseError("ComfyUI response did not contain prompt_id")
        return VideoProviderSubmission(provider_job_id=prompt_id)

    async def result(self, provider_job_id: str) -> VideoProviderResult:
        if not self.base_url:
            raise VideoProviderUnavailableError("VIDEO_BASE_URL is not configured")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(f"{self.base_url}/history/{provider_job_id}")
                response.raise_for_status()
                body = response.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise VideoProviderUnavailableError(str(error)) from error
        except httpx.HTTPError as error:
            raise VideoProviderResponseError(str(error)) from error

        record = body.get(provider_job_id) if isinstance(body, dict) else None
        if not isinstance(record, dict):
            return VideoProviderResult(completed=False, detail="Video generation is still running.")
        outputs = record.get("outputs", {})
        videos: list[GeneratedVideo] = []
        if isinstance(outputs, dict):
            for output in outputs.values():
                if not isinstance(output, dict):
                    continue
                media_items: list[object] = []
                for key in ("videos", "gifs"):
                    value = output.get(key, [])
                    if isinstance(value, list):
                        media_items.extend(value)
                for media in media_items:
                    if not isinstance(media, dict) or not isinstance(media.get("filename"), str):
                        continue
                    query = urlencode(
                        {
                            "filename": media["filename"],
                            "subfolder": media.get("subfolder", ""),
                            "type": media.get("type", "output"),
                        }
                    )
                    videos.append(
                        GeneratedVideo(
                            url=f"{self.base_url}/view?{query}",
                            filename=media["filename"],
                        )
                    )
        if not videos:
            status = record.get("status", {})
            completed = isinstance(status, dict) and status.get("completed") is True
            if completed:
                raise VideoProviderResponseError("ComfyUI completed without video outputs")
            return VideoProviderResult(completed=False, detail="Video generation is still running.")
        return VideoProviderResult(completed=True, videos=videos)

    async def wait_for_result(self, provider_job_id: str) -> VideoProviderResult:
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            result = await self.result(provider_job_id)
            if result.completed:
                return result
            await asyncio.sleep(self.poll_interval_seconds)
        raise VideoProviderUnavailableError("Timed out waiting for ComfyUI video generation")
