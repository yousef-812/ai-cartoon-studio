class VideoProviderError(RuntimeError):
    """Base error for replaceable video-generation providers."""


class VideoProviderUnavailableError(VideoProviderError):
    """Raised when the configured video worker cannot be reached or times out."""


class VideoProviderResponseError(VideoProviderError):
    """Raised when a video provider returns an invalid or failed response."""
