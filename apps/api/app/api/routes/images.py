from fastapi import APIRouter, Depends

from app.dependencies import get_image_provider
from packages.images.comfyui import ComfyUIImageProvider
from packages.images.models import ImageProviderHealth

router = APIRouter()


@router.get("/health", response_model=ImageProviderHealth)
async def image_health(
    provider: ComfyUIImageProvider = Depends(get_image_provider),
) -> ImageProviderHealth:
    return await provider.health()
