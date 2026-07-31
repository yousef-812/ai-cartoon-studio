class LLMProviderError(Exception):
    """Base error raised by a local or self-hosted LLM provider."""


class LLMUnavailableError(LLMProviderError):
    """The configured inference endpoint cannot currently be reached."""


class LLMResponseError(LLMProviderError):
    """The provider returned an invalid or unusable response."""
