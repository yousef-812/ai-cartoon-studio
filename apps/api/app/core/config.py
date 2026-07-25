from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Cartoon Studio API"
    app_env: str = "development"
    database_url: str = "sqlite:///./cartoon_studio.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_path: str = "./storage"
    render_path: str = "./renders"
    cors_origins: list[str] = ["http://localhost:3000"]

    llm_provider: str = "local-openai-compatible"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct-AWQ"
    llm_timeout_seconds: float = 300
    llm_max_retries: int = 2
    llm_json_response_format: bool = True

    image_provider: str = "local-comfyui"
    image_base_url: str = ""
    image_workflow_path: str = "../../workflows/comfyui/sdxl.json"
    image_client_id: str = "ai-cartoon-studio"
    image_timeout_seconds: float = 600
    image_poll_interval_seconds: float = 2

    video_provider: str = "local-comfyui-video"
    video_base_url: str = ""
    video_workflow_path: str = "../../workflows/comfyui/svd.json"
    video_client_id: str = "ai-cartoon-studio-video"
    video_timeout_seconds: float = 1200
    video_poll_interval_seconds: float = 3

    voice_provider: str = "local-openai-compatible-tts"
    voice_base_url: str = ""
    voice_api_key: str = ""
    voice_model: str = "local-tts"
    voice_timeout_seconds: float = 300
    voice_max_retries: int = 2

    lip_sync_provider: str = "local-lip-sync-http"
    lip_sync_base_url: str = ""
    lip_sync_endpoint_path: str = "/v1/lip-sync"
    lip_sync_api_key: str = ""
    lip_sync_timeout_seconds: float = 1200

    celery_task_always_eager: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
