from pathlib import Path

from packages.mixing.ffmpeg import FFmpegSoundMixer
from packages.sound.models import (
    DialogueDuckingWindow,
    GeneratedSoundAsset,
    SoundCueKind,
    SoundCueSpec,
    SoundMixGenerationSpec,
)


def asset(key, kind, path):
    return GeneratedSoundAsset(
        cue_key=key,
        kind=kind,
        prompt=key,
        storage_path=str(path),
    )


def rain_cue(scene, shot, duration):
    return SoundCueSpec(
        key=f"scene:{scene}:shot:{shot}:rain",
        kind=SoundCueKind.AMBIENCE,
        prompt="steady storm rain outside workshop window",
        duration_seconds=duration,
        gain_db=-18,
        loop=True,
    )


def effect_cue(scene, shot, duration, start, text):
    return SoundCueSpec(
        key=f"scene:{scene}:shot:{shot}:effect",
        kind=SoundCueKind.EFFECT,
        prompt=text,
        start_time_seconds=start,
        duration_seconds=min(duration - start, 1.8),
        gain_db=-10,
    )


def make_spec(video, scene, shot, duration, planned):
    return SoundMixGenerationSpec(
        input_video_path=str(video),
        source_has_dialogue=True,
        scene_number=scene,
        shot_number=shot,
        duration_seconds=duration,
        cues=planned,
        dialogue_windows=[
            DialogueDuckingWindow(
                start_time_seconds=0.7,
                end_time_seconds=min(duration, 3.2),
            )
        ],
        target_loudness_lufs=-16,
    )
