from pathlib import Path

from packages.mixing.ffmpeg import FFmpegSoundMixer
from packages.sound.models import GeneratedSoundAsset, SoundCueKind


def asset(key, kind, path):
    return GeneratedSoundAsset(
        cue_key=key,
        kind=kind,
        prompt=key,
        storage_path=str(path),
    )
