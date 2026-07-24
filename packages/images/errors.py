class ImageProviderError(RuntimeError):
    pass


class ImageProviderUnavailableError(ImageProviderError):
    pass


class ImageProviderResponseError(ImageProviderError):
    pass
