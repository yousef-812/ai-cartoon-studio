from fastapi import APIRouter, Depends

from app.dependencies import get_llm_provider
from packages.llm.models import LLMHealth
from packages.llm.openai_compatible import OpenAICompatibleLLMProvider

router = APIRouter()


@router.get("/health", response_model=LLMHealth)
async def llm_health(
    provider: OpenAICompatibleLLMProvider = Depends(get_llm_provider),
) -> LLMHealth:
    return await provider.health()
