from fastapi import APIRouter

from app.api.routes import (
    characters,
    directions,
    health,
    images,
    llm,
    production,
    scripts,
    series,
    stories,
    visuals,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(series.router, prefix="/series", tags=["series"])
api_router.include_router(characters.router, tags=["characters"])
api_router.include_router(stories.router, tags=["stories"])
api_router.include_router(scripts.router, tags=["scripts"])
api_router.include_router(directions.router, tags=["directions"])
api_router.include_router(visuals.router, tags=["visuals"])
api_router.include_router(production.router, prefix="/production", tags=["production"])
