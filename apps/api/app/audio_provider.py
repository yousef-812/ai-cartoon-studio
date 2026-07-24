from app.core.config import settings
from packages.audio.openai_compatible import OpenAICompatibleAudioProvider


def build_audio_provider() -> OpenAICompatibleAudioProvider:
    return OpenAICompatibleAudioProvider(
        base_url=settings.voice_base_url,
        model=settings.voice_model,
        api_key=settings.voice_api_key,
        timeout_seconds=settings.voice_timeout_seconds,
        max_retries=settings.voice_max_retries,
    )
