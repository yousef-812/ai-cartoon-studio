import asyncio
import copy
import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlencode, urlparse

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

MAX_REFERENCE_IMAGE_BYTES = 50 * 1024 * 1024


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

    def render(
        self,
        spec: ImageGenerationSpec,
        *,
        reference_filenames: list[str] | None = None,
    ) -> dict[str, Any]:
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
        references = reference_filenames or []
        if references:
            values["reference_image"] = references[0]
            for index, filename in enumerate(references, start=1):
                values[f"reference_image_{index}"] = filename
            for key in self.bindings:
                if not key.startswith("reference_image_") or key in values:
                    continue
                try:
                    index = int(key.removeprefix("reference_image_"))
                except ValueError:
                    continue
                if index >= 1:
                    values[key] = references[min(index - 1, len(references) - 1)]

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
        reference_workflow_path: str = "",
        client_id: str = "ai-cartoon-studio",
        timeout_seconds: float = 300,
        poll_interval_seconds: float = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.workflow_path = workflow_path
        self.reference_workflow_path = reference_workflow_path
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
            if self.reference_workflow_path:
                ComfyUIWorkflowTemplate.from_file(self.reference_workflow_path)
            return ImageProviderHealth(
                available=True,
                provider=self.name,
                detail="Self-hosted ComfyUI endpoint and workflows are ready.",
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

        reference_filenames: list[str] = []
        workflow_path = self.workflow_path
        if spec.reference_urls:
            if not self.reference_workflow_path:
                raise ImageProviderUnavailableError(
                    "IMAGE_REFERENCE_WORKFLOW_PATH is required for reference-guided generation"
                )
            workflow_path = self.reference_workflow_path
            reference_filenames = await self._upload_reference_images(spec.reference_urls)

        template = ComfyUIWorkflowTemplate.from_file(workflow_path)
        payload = {
            "prompt": template.render(spec, reference_filenames=reference_filenames),
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
            raise ImageProviderUnavailableError(str(error)) from error
        except httpx.HTTPError as error:
            raise ImageProviderResponseError(str(error)) from error
        prompt_id = body.get("prompt_id") if isinstance(body, dict) else None
        if not isinstance(prompt_id, str) or not prompt_id:
            raise ImageProviderResponseError("ComfyUI response did not contain prompt_id")
        return ImageProviderSubmission(provider_job_id=prompt_id)

    async def _upload_reference_images(self, sources: list[str]) -> list[str]:
        uploaded: list[str] = []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                for index, source in enumerate(sources, start=1):
                    content, source_name, mime_type = await self._read_reference(
                        client,
                        source,
                        index,
                    )
                    suffix = Path(source_name).suffix.lower()
                    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                        suffix = ".png"
                    upload_name = f"reference-{index}-{uuid.uuid4().hex[:12]}{suffix}"
                    response = await client.post(
                        f"{self.base_url}/upload/image",
                        data={"overwrite": "true", "type": "input"},
                        files={"image": (upload_name, content, mime_type)},
                    )
                    response.raise_for_status()
                    body = response.json()
                    name = body.get("name") if isinstance(body, dict) else None
                    if not isinstance(name, str) or not name:
                        raise ImageProviderResponseError(
                            "ComfyUI reference upload did not return an image name"
                        )
                    subfolder = body.get("subfolder", "")
                    if isinstance(subfolder, str) and subfolder:
                        name = f"{subfolder.strip('/')}/{name}"
                    uploaded.append(name)
        except ImageProviderResponseError:
            raise
        except (httpx.HTTPError, OSError, ValueError) as error:
            raise ImageProviderResponseError(
                f"Could not stage reference image for ComfyUI: {error}"
            ) from error
        return uploaded

    async def _read_reference(
        self,
        client: httpx.AsyncClient,
        source: str,
        index: int,
    ) -> tuple[bytes, str, str]:
        parsed = urlparse(source)
        if parsed.scheme in {"http", "https"}:
            response = await client.get(source)
            response.raise_for_status()
            content = response.content
            filename = Path(unquote(parsed.path)).name or f"reference-{index}.png"
            mime_type = response.headers.get("content-type", "image/png").split(";", 1)[0]
        elif parsed.scheme == "file":
            path = Path(unquote(parsed.path)).expanduser()
            content = path.read_bytes()
            filename = path.name
            mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        elif not parsed.scheme:
            path = Path(source).expanduser()
            content = path.read_bytes()
            filename = path.name
            mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
        else:
            raise ValueError(f"Unsupported reference image source: {source}")

        if not content:
            raise ValueError(f"Reference image {index} is empty")
        if len(content) > MAX_REFERENCE_IMAGE_BYTES:
            raise ValueError(f"Reference image {index} exceeds 50 MB")
        return content, filename, mime_type

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
