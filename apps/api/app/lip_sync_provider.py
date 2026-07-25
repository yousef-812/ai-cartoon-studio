from app.core.config import settings
from packages.lipsync.http_provider import SelfHostedLipSyncProvider


def build_lip_sync_provider() -> SelfHostedLipSyncProvider:
    return SelfHostedLipSyncProvider(
        base_url=settings.lip_sync_base_url,
        endpoint_path=settings.lip_sync_endpoint_path,
        api_key=settings.lip_sync_api_key,
        timeout_seconds=settings.lip_sync_timeout_seconds,
    )
