from app.core.config import settings
from packages.videos.comfyui import ComfyUIVideoProvider


def build_video_provider() -> ComfyUIVideoProvider:
    return ComfyUIVideoProvider(
        base_url=settings.video_base_url,
        workflow_path=settings.video_workflow_path,
        client_id=settings.video_client_id,
        timeout_seconds=settings.video_timeout_seconds,
        poll_interval_seconds=settings.video_poll_interval_seconds,
    )
