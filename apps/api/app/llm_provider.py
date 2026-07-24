from app.core.config import Settings, settings
from packages.llm.openai_compatible import OpenAICompatibleLLMProvider


def build_llm_provider(config: Settings = settings) -> OpenAICompatibleLLMProvider:
    return OpenAICompatibleLLMProvider(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        model=config.llm_model,
        timeout_seconds=config.llm_timeout_seconds,
        max_retries=config.llm_max_retries,
        use_json_response_format=config.llm_json_response_format,
    )
