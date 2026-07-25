from fastapi import APIRouter

from app.api.routes import (
    animations,
    characters,
    directions,
    health,
    images,
    lipsync,
    llm,
    production,
    scripts,
    series,
    sound,
    stories,
    visuals,
    voices,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(series.router, prefix="/series", tags=["series"])
api_router.include_router(characters.router, tags=["characters"])
api_router.include_router(stories.router, tags=["stories"])
api_router.include_router(scripts.router, tags=["scripts"])
api_router.include_router(sound.router, tags=["sound"])
api_router.include_router(directions.router, tags=["directions"])
api_router.include_router(visuals.router, tags=["visuals"])
api_router.include_router(animations.router, tags=["animations"])
api_router.include_router(voices.router, tags=["voices"])
api_router.include_router(lipsync.router, tags=["lip-sync"])
api_router.include_router(production.router, prefix="/production", tags=["production"])
