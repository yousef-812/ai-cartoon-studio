from app.core.config import settings
from packages.images.comfyui import ComfyUIImageProvider


def build_image_provider() -> ComfyUIImageProvider:
    return ComfyUIImageProvider(
        base_url=settings.image_base_url,
        workflow_path=settings.image_workflow_path,
        client_id=settings.image_client_id,
        timeout_seconds=settings.image_timeout_seconds,
        poll_interval_seconds=settings.image_poll_interval_seconds,
    )
