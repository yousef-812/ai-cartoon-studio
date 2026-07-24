import hashlib

from packages.artifacts.local_store import LocalArtifactStore
from packages.audio.models import SynthesizedAudio


def test_local_artifact_store_persists_voice_audio_with_checksum(tmp_path) -> None:
    content = b"RIFF-fake-wave-content"
    store = LocalArtifactStore(str(tmp_path))

    audio = store.persist_audio(
        SynthesizedAudio(
            content=content,
            filename="speech.wav",
            mime_type="audio/wav",
            duration_seconds=2.5,
            sample_rate=24000,
            channels=1,
        ),
        series_id="series-1",
        voice_job_id="voice-1",
    )

    assert audio.url == "/artifacts/series-1/voice-lines/voice-1/voice.wav"
    assert audio.checksum_sha256 == hashlib.sha256(content).hexdigest()
    assert audio.size_bytes == len(content)
    assert audio.duration_seconds == 2.5
    assert (tmp_path / "series-1" / "voice-lines" / "voice-1" / "voice.wav").read_bytes() == content
