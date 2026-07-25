class SoundProviderError(RuntimeError):
    """Base error raised by sound generation providers."""


class SoundProviderUnavailableError(SoundProviderError):
    """Raised when the configured sound provider cannot be reached."""


class SoundProviderResponseError(SoundProviderError):
    """Raised when the sound provider returns an invalid response."""
