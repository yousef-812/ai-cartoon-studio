from fastapi import APIRouter

from app.api.routes import characters, health, production, series

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(series.router, prefix="/series", tags=["series"])
api_router.include_router(characters.router, tags=["characters"])
api_router.include_router(production.router, prefix="/production", tags=["production"])
