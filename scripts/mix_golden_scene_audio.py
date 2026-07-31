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
        dialogue_windows=[DialogueDuckingWindow(start_time_seconds=0.7, end_time_seconds=min(duration, 3.2))],
        target_loudness_lufs=-16,
    )


def mix_one(video, rain, effect, scene, shot, duration, start, text):
    planned = [rain_cue(scene, shot, duration), effect_cue(scene, shot, duration, start, text)]
    sources = [
        asset(planned[0].key, SoundCueKind.AMBIENCE, rain),
        asset(planned[1].key, SoundCueKind.EFFECT, effect),
    ]
    rendered = FFmpegSoundMixer().mix(make_spec(video, scene, shot, duration, planned), sources)
    video.write_bytes(rendered.content)
    print("GOLDEN_AUDIO_MIXED=" + str(video.resolve()))


def main():
    sequence = Path("output/blender/sequence")
    sound = Path("output/golden-scene/sound")
    mix_one(sequence / "scene_01_shot_01.mp4", sound / "rain.wav", sound / "flicker.wav", 1, 1, 3.2, 0.0, "lamp flicker and electrical failure")
    mix_one(sequence / "scene_01_shot_02.mp4", sound / "rain.wav", sound / "thunder.wav", 1, 2, 4.8, 0.43, "distant thunder after lightning")


if __name__ == "__main__":
    main()
