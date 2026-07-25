from fastapi import Depends
from sqlalchemy.orm import Session

from app.audio_provider import build_audio_provider
from app.db.session import get_db
from app.image_provider import build_image_provider
from app.lip_sync_provider import build_lip_sync_provider
from app.llm_provider import build_llm_provider
from app.repositories.animations import SQLAnimationJobRepository
from app.repositories.characters import SQLCharacterRepository
from app.repositories.directions import SQLDirectionJobRepository
from app.repositories.lipsync import SQLLipSyncJobRepository
from app.repositories.scripts import SQLScriptJobRepository
from app.repositories.series import SQLSeriesRepository
from app.repositories.stories import SQLStoryJobRepository
from app.repositories.visuals import SQLVisualAssetRepository
from app.repositories.voices import SQLVoiceJobRepository
from app.video_provider import build_video_provider
from packages.animations.service import AnimationJobService
from packages.audio.openai_compatible import OpenAICompatibleAudioProvider
from packages.characters.service import CharacterService
from packages.direction.service import DirectionJobService
from packages.images.comfyui import ComfyUIImageProvider
from packages.lipsync.http_provider import SelfHostedLipSyncProvider
from packages.lipsync.service import LipSyncJobService
from packages.llm.openai_compatible import OpenAICompatibleLLMProvider
from packages.scripts.service import ScriptJobService
from packages.series.service import SeriesService
from packages.stories.service import StoryJobService
from packages.videos.comfyui import ComfyUIVideoProvider
from packages.visuals.service import VisualAssetService
from packages.voices.service import VoiceJobService


def get_series_service(session: Session = Depends(get_db)) -> SeriesService:
    return SeriesService(SQLSeriesRepository(session))


def get_character_service(session: Session = Depends(get_db)) -> CharacterService:
    return CharacterService(SQLCharacterRepository(session))


def get_story_job_service(session: Session = Depends(get_db)) -> StoryJobService:
    return StoryJobService(SQLStoryJobRepository(session))


def get_script_job_service(session: Session = Depends(get_db)) -> ScriptJobService:
    return ScriptJobService(SQLScriptJobRepository(session))


def get_direction_job_service(session: Session = Depends(get_db)) -> DirectionJobService:
    return DirectionJobService(SQLDirectionJobRepository(session))


def get_visual_asset_service(session: Session = Depends(get_db)) -> VisualAssetService:
    return VisualAssetService(SQLVisualAssetRepository(session))


def get_animation_job_service(session: Session = Depends(get_db)) -> AnimationJobService:
    visual_repository = SQLVisualAssetRepository(session)
    return AnimationJobService(SQLAnimationJobRepository(session), visual_repository)


def get_voice_job_service(session: Session = Depends(get_db)) -> VoiceJobService:
    return VoiceJobService(SQLVoiceJobRepository(session))


def get_lip_sync_job_service(session: Session = Depends(get_db)) -> LipSyncJobService:
    return LipSyncJobService(
        SQLLipSyncJobRepository(session),
        SQLAnimationJobRepository(session),
        SQLVoiceJobRepository(session),
    )


def get_llm_provider() -> OpenAICompatibleLLMProvider:
    return build_llm_provider()


def get_image_provider() -> ComfyUIImageProvider:
    return build_image_provider()


def get_video_provider() -> ComfyUIVideoProvider:
    return build_video_provider()


def get_audio_provider() -> OpenAICompatibleAudioProvider:
    return build_audio_provider()


def get_lip_sync_provider() -> SelfHostedLipSyncProvider:
    return build_lip_sync_provider()
