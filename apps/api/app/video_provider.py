from app.core.config import settings
from packages.blender.provider import LocalBlenderVideoProvider
from packages.videos.comfyui import ComfyUIVideoProvider
from packages.videos.provider import VideoProvider


def build_video_provider() -> VideoProvider:
    if settings.video_provider == "local-blender":
        return LocalBlenderVideoProvider(
            blender_binary=settings.blender_binary,
            runner_script=settings.blender_runner_script,
            jobs_path=settings.blender_jobs_path,
            timeout_seconds=settings.blender_timeout_seconds,
        )
    return ComfyUIVideoProvider(
        base_url=settings.video_base_url,
        workflow_path=settings.video_workflow_path,
        client_id=settings.video_client_id,
        timeout_seconds=settings.video_timeout_seconds,
        poll_interval_seconds=settings.video_poll_interval_seconds,
    )
