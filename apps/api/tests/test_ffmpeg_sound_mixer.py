from pathlib import Path

from packages.mixing.ffmpeg import FFmpegSoundMixer
from packages.sound.models import (
    DialogueDuckingWindow,
    GeneratedSoundAsset,
    SoundCueKind,
    SoundCueSpec,
    SoundMixGenerationSpec,
)


def test_ffmpeg_mixer_builds_ducked_loudness_normalized_command(tmp_path) -> None:
    source = tmp_path / "source.mp4"
    ambience = tmp_path / "ambience.wav"
    music = tmp_path / "music.wav"
    source.write_bytes(b"video")
    ambience.write_bytes(b"ambience")
    music.write_bytes(b"music")
    cues = [
        SoundCueSpec(
            key="scene:1:shot:1:ambience",
            kind=SoundCueKind.AMBIENCE,
            prompt="Room tone.",
            duration_seconds=5,
            gain_db=-20,
            loop=True,
        ),
        SoundCueSpec(
            key="scene:1:shot:1:music",
            kind=SoundCueKind.MUSIC,
            prompt="Instrumental score.",
            duration_seconds=5,
            gain_db=-22,
            loop=True,
        ),
    ]
    assets = [
        GeneratedSoundAsset(
            cue_key=cues[0].key,
            kind=cues[0].kind,
            prompt=cues[0].prompt,
            storage_path=str(ambience),
        ),
        GeneratedSoundAsset(
            cue_key=cues[1].key,
            kind=cues[1].kind,
            prompt=cues[1].prompt,
            storage_path=str(music),
        ),
    ]
    spec = SoundMixGenerationSpec(
        input_video_path=str(source),
        source_has_dialogue=True,
        scene_number=1,
        shot_number=1,
        duration_seconds=5,
        cues=cues,
        dialogue_windows=[
            DialogueDuckingWindow(start_time_seconds=0.5, end_time_seconds=2.5)
        ],
        dialogue_ducking_db=-10,
        target_loudness_lufs=-16,
    )

    command = FFmpegSoundMixer().build_command(spec, assets, str(tmp_path / "out.mp4"))
    filter_complex = command[command.index("-filter_complex") + 1]

    assert "volume=-10.00dB:enable='between(t,0.500,2.500)'" in filter_complex
    assert "loudnorm=I=-16.00" in filter_complex
    assert command.count("-stream_loop") == 2
    assert Path(command[-1]).name == "out.mp4"
