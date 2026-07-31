from app.core.config import settings
from packages.sound.http_provider import SelfHostedSoundProvider


def build_sound_provider() -> SelfHostedSoundProvider:
    return SelfHostedSoundProvider(
        base_url=settings.sound_base_url,
        endpoint_path=settings.sound_endpoint_path,
        api_key=settings.sound_api_key,
        timeout_seconds=settings.sound_timeout_seconds,
    )
