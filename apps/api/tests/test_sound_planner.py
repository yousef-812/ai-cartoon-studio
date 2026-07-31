from types import SimpleNamespace

from packages.animations.models import AnimationJobStatus, AnimationReviewStatus
from packages.lipsync.models import LipSyncJobStatus, LipSyncReviewStatus
from packages.sound.models import SoundCueKind, SoundPlanRequest
from packages.sound.planner import SoundDesignPlanner


def _shot(scene: int, number: int, dialogue: list[int]) -> SimpleNamespace:
    return SimpleNamespace(
        scene_number=scene,
        number=number,
        duration_seconds=4.0,
        location="workshop",
        action="Mira places a humming device on the table.",
        emotion="careful optimism",
        shot_size="medium shot",
        transition="cut",
        characters=["Mira"],
        dialogue_line_orders=dialogue,
    )


def test_sound_planner_uses_lip_sync_for_dialogue_and_animation_for_silence(tmp_path) -> None:
    speaking_video = tmp_path / "speaking.mp4"
    silent_video = tmp_path / "silent.mp4"
    speaking_video.write_bytes(b"speaking")
    silent_video.write_bytes(b"silent")
    direction = SimpleNamespace(
        title="The Stable Engine",
        scenes=[
            SimpleNamespace(scene_number=1, title="Workshop", shots=[_shot(1, 1, [1])]),
            SimpleNamespace(scene_number=2, title="Hallway", shots=[_shot(2, 1, [])]),
        ],
    )
    animation = SimpleNamespace(
        id="animation-2",
        status=AnimationJobStatus.SUCCEEDED,
        review_status=AnimationReviewStatus.APPROVED,
        spec=SimpleNamespace(scene_number=2, shot_number=1),
        videos=[SimpleNamespace(storage_path=str(silent_video))],
    )
    lip_sync = SimpleNamespace(
        id="lip-1",
        status=LipSyncJobStatus.SUCCEEDED,
        review_status=LipSyncReviewStatus.APPROVED,
        spec=SimpleNamespace(
            generation=SimpleNamespace(
                scene_number=1,
                shot_number=1,
                segments=[SimpleNamespace(start_time_seconds=0.4, end_time_seconds=2.4)],
            )
        ),
        videos=[SimpleNamespace(storage_path=str(speaking_video))],
    )

    specs = SoundDesignPlanner().plan(
        direction,
        [animation],
        [lip_sync],
        SoundPlanRequest(),
    )

    assert len(specs) == 2
    assert specs[0].source_job_type == "lip_sync"
    assert specs[0].generation.source_has_dialogue is True
    assert specs[0].generation.dialogue_windows[0].start_time_seconds == 0.4
    assert specs[1].source_job_type == "animation"
    assert specs[1].generation.source_has_dialogue is False
    assert {cue.kind for cue in specs[0].generation.cues} == {
        SoundCueKind.AMBIENCE,
        SoundCueKind.EFFECT,
        SoundCueKind.MUSIC,
    }
