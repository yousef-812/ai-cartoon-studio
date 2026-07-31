class SoundProviderError(RuntimeError):
    pass


class SoundProviderUnavailableError(SoundProviderError):
    pass


class SoundProviderResponseError(SoundProviderError):
    pass


class SoundMixError(RuntimeError):
    pass


class SoundMixUnavailableError(SoundMixError):
    pass
