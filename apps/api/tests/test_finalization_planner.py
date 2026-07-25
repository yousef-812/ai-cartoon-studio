from types import SimpleNamespace

import pytest

from packages.finalization.models import FinalizationPlanRequest
from packages.finalization.planner import FinalizationPlanner
from packages.sound.models import SoundMixJobStatus, SoundMixReviewStatus


def _sound_job(
    tmp_path,
    *,
    job_id: str,
    scene_number: int,
    shot_number: int,
    source_type: str,
    source_job_id: str,
    duration: float,
    approved: bool = True,
):
    video_path = tmp_path / f"{job_id}.mp4"
    video_path.write_bytes(b"video")
    return SimpleNamespace(
        id=job_id,
        status=SoundMixJobStatus.SUCCEEDED,
        review_status=(
            SoundMixReviewStatus.APPROVED
            if approved
            else SoundMixReviewStatus.PENDING_REVIEW
        ),
        source_job_type=source_type,
        source_job_id=source_job_id,
        spec=SimpleNamespace(
            generation=SimpleNamespace(
                scene_number=scene_number,
                shot_number=shot_number,
            )
        ),
        videos=[
            SimpleNamespace(
                storage_path=str(video_path),
                duration_seconds=duration,
            )
        ],
    )


def test_finalization_planner_builds_timeline_subtitles_and_short(tmp_path) -> None:
    direction = SimpleNamespace(
        title="The Final Circuit",
        scenes=[
            SimpleNamespace(
                scene_number=1,
                title="Workshop reveal",
                shots=[
                    SimpleNamespace(
                        number=1,
                        duration_seconds=4.0,
                        transition="cut",
                    ),
                    SimpleNamespace(
                        number=2,
                        duration_seconds=4.0,
                        transition="cut",
                    ),
                ],
            )
        ],
    )
    speaking = _sound_job(
        tmp_path,
        job_id="sound-1",
        scene_number=1,
        shot_number=1,
        source_type="lip_sync",
        source_job_id="lip-1",
        duration=4.0,
    )
    silent = _sound_job(
        tmp_path,
        job_id="sound-2",
        scene_number=1,
        shot_number=2,
        source_type="animation",
        source_job_id="animation-2",
        duration=4.0,
    )
    lip_sync = SimpleNamespace(
        id="lip-1",
        spec=SimpleNamespace(
            generation=SimpleNamespace(
                segments=[
                    SimpleNamespace(
                        start_time_seconds=0.5,
                        end_time_seconds=2.5,
                        text="The circuit is stable.",
                        character_name="Mira",
                    )
                ]
            )
        ),
    )

    spec = FinalizationPlanner().plan(
        "direction-1",
        direction,
        [speaking, silent],
        [lip_sync],
        FinalizationPlanRequest(
            shorts_candidate_count=1,
            shorts_duration_seconds=10,
        ),
    )

    assert spec.total_duration_seconds == 8.0
    assert spec.shots[0].timeline_start_seconds == 0.0
    assert spec.shots[1].timeline_start_seconds == 4.0
    assert spec.subtitles[0].start_time_seconds == 0.5
    assert spec.subtitles[0].speaker == "Mira"
    assert spec.short_candidates[0].duration_seconds == 8.0
    assert spec.preflight_report.passed is True


def test_finalization_planner_rejects_unapproved_sound_mix(tmp_path) -> None:
    direction = SimpleNamespace(
        title="Blocked episode",
        scenes=[
            SimpleNamespace(
                scene_number=1,
                title="Scene",
                shots=[
                    SimpleNamespace(
                        number=1,
                        duration_seconds=5.0,
                        transition="cut",
                    )
                ],
            )
        ],
    )
    sound = _sound_job(
        tmp_path,
        job_id="sound-1",
        scene_number=1,
        shot_number=1,
        source_type="animation",
        source_job_id="animation-1",
        duration=5.0,
        approved=False,
    )

    with pytest.raises(ValueError, match="approved"):
        FinalizationPlanner().plan(
            "direction-1",
            direction,
            [sound],
            [],
            FinalizationPlanRequest(shorts_candidate_count=0),
        )
