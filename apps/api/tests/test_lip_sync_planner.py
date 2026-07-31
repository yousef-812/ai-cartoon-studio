import pytest

from packages.animations.models import (
    AnimatedShotSpec,
    AnimationJobRead,
    AnimationJobStatus,
    AnimationReviewStatus,
)
from packages.audio.models import GeneratedAudio, SpeechSynthesisSpec
from packages.direction.models import EpisodeDirection
from packages.lipsync.models import LipSyncPlanRequest
from packages.lipsync.planner import LipSyncPlanner
from packages.videos.models import GeneratedVideo, VideoGenerationSpec
from packages.voices.models import (
    VoiceJobRead,
    VoiceJobStatus,
    VoiceLineSpec,
    VoiceReviewStatus,
)


def test_lip_sync_planner_places_multiple_speakers_without_overlap(tmp_path) -> None:
    video_path = tmp_path / "shot.mp4"
    mira_audio = tmp_path / "mira.wav"
    nico_audio = tmp_path / "nico.wav"
    video_path.write_bytes(b"video")
    mira_audio.write_bytes(b"mira")
    nico_audio.write_bytes(b"nico")

    direction = EpisodeDirection(
        title="The Clockwork Cloud",
        total_estimated_duration_seconds=60,
        scenes=[
            {
                "scene_number": 1,
                "title": "Engine Room",
                "estimated_duration_seconds": 20,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 1,
                        "duration_seconds": 20,
                        "shot_size": "medium two shot",
                        "camera_angle": "eye level",
                        "camera_movement": "locked camera",
                        "composition": "Mira and Nico remain visible with readable faces.",
                        "location": "Engine Room",
                        "characters": ["Mira", "Nico"],
                        "action": "They inspect the repaired cloud engine.",
                        "emotion": "relief",
                        "dialogue_line_orders": [1, 2],
                        "visual_prompt": "Stylized animation frame inside a warm engine room.",
                    }
                ],
            },
            {
                "scene_number": 2,
                "title": "Market",
                "estimated_duration_seconds": 20,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 2,
                        "duration_seconds": 20,
                        "shot_size": "wide",
                        "camera_angle": "high angle",
                        "camera_movement": "slow pan",
                        "composition": "The market settles beneath the clouds.",
                        "location": "Cloud Market",
                        "characters": [],
                        "action": "Stalls return to the ground.",
                        "emotion": "calm",
                        "visual_prompt": "Wide stylized animation background of a cloud market.",
                    }
                ],
            },
            {
                "scene_number": 3,
                "title": "Workshop",
                "estimated_duration_seconds": 20,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 3,
                        "duration_seconds": 20,
                        "shot_size": "close up",
                        "camera_angle": "eye level",
                        "camera_movement": "slow push in",
                        "composition": "A repaired control label fills the frame.",
                        "location": "Workshop",
                        "characters": [],
                        "action": "The indicator glows steadily.",
                        "emotion": "resolved",
                        "visual_prompt": "Close production frame of a repaired control panel.",
                    }
                ],
            },
        ],
    )
    animation = AnimationJobRead(
        id="animation-1",
        series_id="series-1",
        direction_job_id="direction-1",
        keyframe_asset_id="asset-1",
        status=AnimationJobStatus.SUCCEEDED,
        review_status=AnimationReviewStatus.APPROVED,
        provider="local-comfyui-video",
        attempts=1,
        spec=AnimatedShotSpec(
            key="scene:1:shot:1:animation",
            scene_number=1,
            shot_number=1,
            keyframe_asset_id="asset-1",
            generation=VideoGenerationSpec(
                input_image_path=str(tmp_path / "keyframe.png"),
                prompt="Animate both characters with subtle natural motion.",
                duration_seconds=20,
                fps=16,
            ),
        ),
        videos=[
            GeneratedVideo(
                url="/artifacts/shot.mp4",
                filename="shot.mp4",
                storage_path=str(video_path),
                duration_seconds=20,
            )
        ],
    )
    voices = [
        _voice_job("voice-1", "Mira", 1, str(mira_audio), 2.0, 300),
        _voice_job("voice-2", "Nico", 2, str(nico_audio), 3.0, 200),
    ]

    specs = LipSyncPlanner().plan(
        direction,
        [animation],
        voices,
        LipSyncPlanRequest(lead_in_ms=250, minimum_gap_ms=120),
    )

    assert len(specs) == 1
    segments = specs[0].generation.segments
    assert segments[0].start_time_seconds == pytest.approx(0.25)
    assert segments[0].end_time_seconds == pytest.approx(2.25)
    assert segments[1].start_time_seconds == pytest.approx(2.55)
    assert segments[1].end_time_seconds == pytest.approx(5.55)
    assert segments[0].character_name == "Mira"
    assert segments[1].character_name == "Nico"


def _voice_job(
    job_id: str,
    character_name: str,
    order: int,
    storage_path: str,
    duration: float,
    pause_after_ms: int,
) -> VoiceJobRead:
    return VoiceJobRead(
        id=job_id,
        series_id="series-1",
        script_job_id="script-1",
        character_id=f"character-{order}",
        status=VoiceJobStatus.SUCCEEDED,
        review_status=VoiceReviewStatus.APPROVED,
        provider="local-tts",
        attempts=1,
        spec=VoiceLineSpec(
            key=f"scene:1:dialogue:{order}:voice",
            scene_number=1,
            dialogue_order=order,
            character_id=f"character-{order}",
            character_name=character_name,
            pause_after_ms=pause_after_ms,
            synthesis=SpeechSynthesisSpec(
                text=f"Dialogue line {order} for the repaired engine.",
                voice_id=f"{character_name.lower()}-main",
                emotion="relieved",
                delivery="clear and warm",
                target_duration_seconds=duration,
            ),
        ),
        audio=GeneratedAudio(
            url=f"/artifacts/{job_id}.wav",
            filename=f"{job_id}.wav",
            storage_path=storage_path,
            duration_seconds=duration,
        ),
    )
