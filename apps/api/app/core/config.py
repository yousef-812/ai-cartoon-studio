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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
