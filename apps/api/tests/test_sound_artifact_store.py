from packages.sound.models import (
    RenderedSoundAsset,
    RenderedSoundMix,
    SoundCueKind,
    SoundCueSpec,
)
from packages.sound.storage import SoundArtifactStore


def test_sound_artifact_store_persists_assets_and_mix(tmp_path) -> None:
    store = SoundArtifactStore(str(tmp_path))
    cue = SoundCueSpec(
        key="scene:1:shot:1:music",
        kind=SoundCueKind.MUSIC,
        prompt="Soft instrumental tension cue.",
        duration_seconds=3,
    )
    asset = store.persist_asset(
        RenderedSoundAsset(
            content=b"audio-bytes",
            filename="music.wav",
            mime_type="audio/wav",
            duration_seconds=3,
        ),
        cue,
        series_id="series-1",
        job_id="sound-1",
        index=1,
    )
    video = store.persist_mix(
        RenderedSoundMix(
            content=b"video-bytes",
            filename="mix.mp4",
            mime_type="video/mp4",
            duration_seconds=3,
        ),
        series_id="series-1",
        job_id="sound-1",
    )

    assert asset.url.startswith("/artifacts/series-1/sound-assets/")
    assert asset.checksum_sha256
    assert video.url.startswith("/artifacts/series-1/sound-mixes/")
    assert video.checksum_sha256
