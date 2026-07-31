import asyncio
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import BinaryIO

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


class LocalBlenderVideoProvider:
    name = "local-blender"

    def __init__(
        self,
        *,
        blender_binary: str = "blender",
        runner_script: str,
        jobs_path: str,
        timeout_seconds: float = 1800,
    ) -> None:
        self.blender_binary = blender_binary
        self.runner_script = str(Path(runner_script).expanduser().resolve())
        self.jobs_path = Path(jobs_path).expanduser().resolve()
        self.timeout_seconds = timeout_seconds
        self._processes: dict[str, subprocess.Popen[bytes]] = {}
        self._logs: dict[str, BinaryIO] = {}
        self._specs: dict[str, VideoGenerationSpec] = {}

    async def health(self) -> VideoProviderHealth:
        runner = Path(self.runner_script)
        if not runner.is_file():
            return VideoProviderHealth(
                available=False,
                provider=self.name,
                detail=f"Blender runner script does not exist: {runner}",
            )
        try:
            completed = await asyncio.to_thread(
                subprocess.run,
                [self.blender_binary, "--version"],
                capture_output=True,
                check=False,
                timeout=30,
            )
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as error:
            return VideoProviderHealth(
                available=False,
                provider=self.name,
                detail=str(error),
            )
        output = (completed.stdout or b"") + (completed.stderr or b"")
        if completed.returncode != 0:
            return VideoProviderHealth(
                available=False,
                provider=self.name,
                detail=output.decode("utf-8", errors="replace")[-2000:],
            )
        first_line = output.decode("utf-8", errors="replace").splitlines()
        detail = first_line[0] if first_line else "Blender is ready."
        return VideoProviderHealth(available=True, provider=self.name, detail=detail)

    async def submit(self, spec: VideoGenerationSpec) -> VideoProviderSubmission:
        scene_path = Path(spec.input_scene_path).expanduser().resolve()
        if not scene_path.is_file():
            raise VideoProviderResponseError(f"Blender scene does not exist: {scene_path}")
        runner = Path(self.runner_script)
        if not runner.is_file():
            raise VideoProviderUnavailableError(f"Blender runner script does not exist: {runner}")

        manifest = spec.metadata.get("blender_manifest")
        if not isinstance(manifest, dict):
            raise VideoProviderResponseError(
                "Blender video generation requires metadata.blender_manifest"
            )

        job_id = uuid.uuid4().hex
        job_dir = self.jobs_path / job_id
        job_dir.mkdir(parents=True, exist_ok=False)
        manifest_path = job_dir / "shot.json"
        output_path = job_dir / "shot.mp4"
        log_path = job_dir / "blender.log"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        log_file = log_path.open("wb")
        command = [
            self.blender_binary,
            "--background",
            str(scene_path),
            "--python",
            str(runner),
            "--",
            "--manifest",
            str(manifest_path),
            "--output",
            str(output_path),
        ]
        try:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
            )
        except (FileNotFoundError, OSError) as error:
            log_file.close()
            raise VideoProviderUnavailableError(str(error)) from error

        self._processes[job_id] = process
        self._logs[job_id] = log_file
        self._specs[job_id] = spec
        return VideoProviderSubmission(provider_job_id=job_id)

    async def result(self, provider_job_id: str) -> VideoProviderResult:
        process = self._processes.get(provider_job_id)
        if process is None:
            return self._result_from_disk(provider_job_id)
        return_code = process.poll()
        if return_code is None:
            return VideoProviderResult(completed=False, detail="Blender render is still running.")
        return self._completed_result(provider_job_id, return_code)

    async def wait_for_result(self, provider_job_id: str) -> VideoProviderResult:
        process = self._processes.get(provider_job_id)
        if process is None:
            result = self._result_from_disk(provider_job_id)
            if result.completed:
                return result
            raise VideoProviderResponseError("Unknown Blender provider job")
        try:
            return_code = await asyncio.to_thread(process.wait, self.timeout_seconds)
        except subprocess.TimeoutExpired as error:
            process.kill()
            await asyncio.to_thread(process.wait, 30)
            self._close_log(provider_job_id)
            raise VideoProviderUnavailableError("Timed out waiting for Blender render") from error
        return self._completed_result(provider_job_id, return_code)

    def _completed_result(self, provider_job_id: str, return_code: int) -> VideoProviderResult:
        self._close_log(provider_job_id)
        job_dir = self.jobs_path / provider_job_id
        output_path = job_dir / "shot.mp4"
        log_path = job_dir / "blender.log"
        if return_code != 0:
            detail = self._tail(log_path)
            raise VideoProviderResponseError(
                f"Blender exited with code {return_code}.\n{detail}"
            )
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise VideoProviderResponseError(
                "Blender completed without a non-empty MP4 output.\n" + self._tail(log_path)
            )
        spec = self._specs.get(provider_job_id)
        return VideoProviderResult(
            completed=True,
            videos=[
                GeneratedVideo(
                    filename=output_path.name,
                    storage_path=str(output_path),
                    mime_type="video/mp4",
                    size_bytes=output_path.stat().st_size,
                    duration_seconds=spec.duration_seconds if spec else None,
                    fps=float(spec.fps) if spec else None,
                    width=spec.width if spec else None,
                    height=spec.height if spec else None,
                    metadata={"provider_job_id": provider_job_id, "engine": "blender"},
                )
            ],
        )

    def _result_from_disk(self, provider_job_id: str) -> VideoProviderResult:
        output_path = self.jobs_path / provider_job_id / "shot.mp4"
        if not output_path.is_file() or output_path.stat().st_size == 0:
            return VideoProviderResult(completed=False, detail="Blender render is not available.")
        return VideoProviderResult(
            completed=True,
            videos=[
                GeneratedVideo(
                    filename=output_path.name,
                    storage_path=str(output_path),
                    mime_type="video/mp4",
                    size_bytes=output_path.stat().st_size,
                    metadata={"provider_job_id": provider_job_id, "engine": "blender"},
                )
            ],
        )

    def _close_log(self, provider_job_id: str) -> None:
        log_file = self._logs.pop(provider_job_id, None)
        if log_file is not None and not log_file.closed:
            log_file.close()

    @staticmethod
    def _tail(path: Path, limit: int = 8000) -> str:
        if not path.is_file():
            return "Blender log is missing."
        content = path.read_text(encoding="utf-8", errors="replace")
        return content[-limit:]
