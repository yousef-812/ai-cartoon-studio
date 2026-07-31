class LipSyncProviderError(RuntimeError):
    """Base error raised by a lip-sync provider."""


class LipSyncProviderUnavailableError(LipSyncProviderError):
    """Raised when the configured lip-sync worker cannot be reached."""


class LipSyncProviderResponseError(LipSyncProviderError):
    """Raised when a lip-sync worker returns an invalid response."""
