import asyncio
import copy
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field

from packages.images.errors import (
    ImageProviderResponseError,
    ImageProviderUnavailableError,
)
from packages.images.models import (
    GeneratedImage,
    ImageGenerationSpec,
    ImageProviderHealth,
    ImageProviderResult,
    ImageProviderSubmission,
)


class WorkflowBinding(BaseModel):
    node_id: str
    input_name: str


class ComfyUIWorkflowTemplate(BaseModel):
    workflow: dict[str, Any]
    bindings: dict[str, WorkflowBinding] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "ComfyUIWorkflowTemplate":
        if not path:
            raise ImageProviderUnavailableError("IMAGE_WORKFLOW_PATH is not configured")
        try:
            return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ImageProviderUnavailableError(f"Could not load ComfyUI workflow: {error}") from error

    def render(self, spec: ImageGenerationSpec) -> dict[str, Any]:
        workflow = copy.deepcopy(self.workflow)
        values: dict[str, object] = {
            "prompt": spec.prompt,
            "negative_prompt": spec.negative_prompt,
            "width": spec.width,
            "height": spec.height,
            "seed": spec.seed,
            "steps": spec.steps,
            "guidance_scale": spec.guidance_scale,
        }
        for key, value in values.items():
            binding = self.bindings.get(key)
            if binding is None:
                continue
            try:
                workflow[binding.node_id]["inputs"][binding.input_name] = value
            except (KeyError, TypeError) as error:
                raise ImageProviderResponseError(
                    f"Invalid ComfyUI binding for '{key}' at node {binding.node_id}"
                ) from error
        return workflow


class ComfyUIImageProvider:
    name = "local-comfyui"

    def __init__(
        self,
        *,
        base_url: str,
        workflow_path: str,
        client_id: str = "ai-cartoon-studio",
        timeout_seconds: float = 300,
        poll_interval_seconds: float = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_path = workflow_path
        self.client_id = client_id
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.transport = transport

    async def health(self) -> ImageProviderHealth:
        if not self.base_url:
            return ImageProviderHealth(
                available=False,
                provider=self.name,
                detail="IMAGE_BASE_URL is not configured.",
            )
        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.get(f"{self.base_url}/system_stats")
                response.raise_for_status()
            ComfyUIWorkflowTemplate.from_file(self.workflow_path)
            return ImageProviderHealth(
                available=True,
                provider=self.name,
                detail="Self-hosted ComfyUI endpoint and workflow are ready.",
            )
        except (httpx.HTTPError, ImageProviderUnavailableError) as error:
            return ImageProviderHealth(
                available=False,
                provider=self.name,
                detail=str(error),
            )

    async def submit(self, spec: ImageGenerationSpec) -> ImageProviderSubmission:
        if not self.base_url:
            raise ImageProviderUnavailableError("IMAGE_BASE_URL is not configured")
        template = ComfyUIWorkflowTemplate.from_file(self.workflow_path)
        payload = {"prompt": template.render(spec), "client_id": self.client_id}
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.post(f"{self.base_url}/prompt", json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise ImageProviderUnavailableError(str(error)) from error
        except httpx.HTTPError as error:
            raise ImageProviderResponseError(str(error)) from error
        prompt_id = body.get("prompt_id") if isinstance(body, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ImageProviderResponseError("ComfyUI response did not contain prompt_id")
        return ImageProviderSubmission(provider_job_id=prompt_id)

    async def result(self, provider_job_id: str) -> ImageProviderResult:
        if not self.base_url:
            raise ImageProviderUnavailableError("IMAGE_BASE_URL is not configured")
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = await client.get(f"{self.base_url}/history/{provider_job_id}")
                response.raise_for_status()
                body = response.json()
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError) as error:
            raise ImageProviderUnavailableError(str(error)) from error
        except httpx.HTTPError as error:
            raise ImageProviderResponseError(str(error)) from error

        record = body.get(provider_job_id) if isinstance(body, dict) else None
        if not isinstance(record, dict):
            return ImageProviderResult(completed=False, detail="Generation is still running.")
        outputs = record.get("outputs", {})
        images: list[GeneratedImage] = []
        if isinstance(outputs, dict):
            for output in outputs.values():
                if not isinstance(output, dict):
                    continue
                for image in output.get("images", []):
                    if not isinstance(image, dict) or not isinstance(image.get("filename"), str):
                        continue
                    query = urlencode(
                        {
                            "filename": image["filename"],
                            "subfolder": image.get("subfolder", ""),
                            "type": image.get("type", "output"),
                        }
                    )
                    images.append(
                        GeneratedImage(
                            url=f"{self.base_url}/view?{query}",
                            filename=image["filename"],
                        )
                    )
        if not images:
            status = record.get("status", {})
            completed = isinstance(status, dict) and status.get("completed") is True
            if completed:
                raise ImageProviderResponseError("ComfyUI completed without image outputs")
            return ImageProviderResult(completed=False, detail="Generation is still running.")
        return ImageProviderResult(completed=True, images=images)

    async def wait_for_result(self, provider_job_id: str) -> ImageProviderResult:
        deadline = asyncio.get_running_loop().time() + self.timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            result = await self.result(provider_job_id)
            if result.completed:
                return result
            await asyncio.sleep(self.poll_interval_seconds)
        raise ImageProviderUnavailableError("Timed out waiting for ComfyUI image generation")


def load_workflow_template(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
