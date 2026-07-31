class AudioProviderError(RuntimeError):
    """Base error for self-hosted speech providers."""


class AudioProviderUnavailableError(AudioProviderError):
    """Raised when the configured speech worker cannot be reached."""


class AudioProviderResponseError(AudioProviderError):
    """Raised when a speech provider returns an invalid response."""
