from packages.finalization.ffmpeg import build_concat_command, build_short_command
from packages.finalization.models import (
    FinalShotSpec,
    FinalizationJobSpec,
    FinalizationPlanRequest,
    QCReport,
    ShortCandidateSpec,
)


def _spec() -> FinalizationJobSpec:
    return FinalizationJobSpec(
        title="Final episode",
        direction_job_id="direction-1",
        shots=[
            FinalShotSpec(
                sound_job_id="sound-1",
                scene_number=1,
                shot_number=1,
                input_video_path="/tmp/shot.mp4",
                duration_seconds=5.0,
                timeline_start_seconds=0.0,
                timeline_end_seconds=5.0,
            )
        ],
        total_duration_seconds=5.0,
        request=FinalizationPlanRequest(
            output_width=1280,
            output_height=720,
            output_fps=24,
            target_loudness_lufs=-16,
            max_peak_db=-1,
            shorts_candidate_count=0,
        ),
        preflight_report=QCReport(passed=True),
    )


def test_final_concat_command_normalizes_video_and_audio() -> None:
    command = build_concat_command("shots.txt", "episode.mp4", _spec())

    assert "scale=1280:720" in command[command.index("-vf") + 1]
    assert "fps=24" in command[command.index("-vf") + 1]
    assert "loudnorm=I=-16.0:TP=-1.0:LRA=11" == command[command.index("-af") + 1]
    assert command[-1] == "episode.mp4"


def test_short_command_creates_vertical_export() -> None:
    candidate = ShortCandidateSpec(
        index=1,
        start_time_seconds=12.0,
        duration_seconds=30.0,
        title="Reveal",
        scene_number=2,
    )

    command = build_short_command("episode.mp4", "short.mp4", candidate)

    assert command[command.index("-ss") + 1] == "12.000"
    assert command[command.index("-t") + 1] == "30.000"
    assert "scale=1080:1920" in command[command.index("-vf") + 1]
