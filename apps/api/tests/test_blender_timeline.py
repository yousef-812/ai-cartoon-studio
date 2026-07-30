from pathlib import Path

import pytest
from pydantic import ValidationError

from packages.blender.batch import build_episode_manifests
from packages.blender.models import (
    BlenderSceneRegistry,
    BlenderShotManifest,
    CameraCue,
    RenderSettings,
    ShotTimelineOverrides,
    TimelineCue,
)
from packages.direction.models import EpisodeDirection
from packages.scripts.models import EpisodeScript

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "demo" / "first-real-episode"


def _sources() -> tuple[EpisodeDirection, EpisodeScript, BlenderSceneRegistry]:
    direction = EpisodeDirection.model_validate_json(
        (DEMO / "approved" / "direction.json").read_text(encoding="utf-8")
    )
    screenplay = EpisodeScript.model_validate_json(
        (DEMO / "approved" / "screenplay.json").read_text(encoding="utf-8")
    )
    registry = BlenderSceneRegistry.model_validate_json(
        (DEMO / "blender" / "scene_registry.json").read_text(encoding="utf-8")
    )
    return direction, screenplay, registry


def test_golden_scene_timeline_is_injected_by_shot_key() -> None:
    direction, screenplay, registry = _sources()
    overrides = ShotTimelineOverrides.model_validate_json(
        (DEMO / "golden-scene" / "timeline.json").read_text(encoding="utf-8")
    )

    manifests = build_episode_manifests(
        direction,
        screenplay,
        registry,
        timeline_by_shot=overrides.shots,
    )

    assert [cue.kind for cue in manifests[0].timeline] == [
        "light_flicker",
        "light_flicker",
        "light_flicker",
        "camera_push",
    ]
    assert [cue.kind for cue in manifests[1].timeline] == [
        "light_energy",
        "light_flicker",
        "character_look",
        "character_look",
        "character_look",
        "camera_push",
    ]
    assert manifests[2].timeline == []
    assert manifests[0].metadata["timeline_cue_count"] == 4
    assert manifests[1].metadata["timeline_cue_count"] == 6


def test_timeline_rejects_unsupported_cue_kind() -> None:
    with pytest.raises(ValidationError, match="Unsupported Blender timeline cue kind"):
        TimelineCue(
            kind="random_magic",
            target_object="LIGHT_Key",
            start_seconds=0,
        )


def test_character_look_requires_a_focus_object() -> None:
    with pytest.raises(ValidationError, match="require a focus_object"):
        TimelineCue(
            kind="character_look",
            target_object="Nader_Rig",
            start_seconds=0.1,
            duration_seconds=0.4,
            parameters={"max_yaw_degrees": 45},
        )


def test_manifest_rejects_timeline_cue_outside_shot_duration() -> None:
    cue = TimelineCue(
        kind="light_flicker",
        target_object="LIGHT_Key",
        start_seconds=1.5,
        duration_seconds=1.0,
        values=[1.0, 0.0],
    )

    with pytest.raises(ValidationError, match="exceeds the shot duration"):
        BlenderShotManifest(
            scene_number=1,
            shot_number=1,
            shot_key="scene:1:shot:1",
            render=RenderSettings(duration_seconds=2.0),
            camera=CameraCue(
                preset="medium",
                object_name="CAM_Medium",
                look_at_object="ANCHOR_Workbench_Center",
            ),
            timeline=[cue],
        )


def test_blender_executor_applies_timeline_after_camera_setup() -> None:
    source = (ROOT / "workers" / "blender" / "shot_executor.py").read_text(
        encoding="utf-8"
    )

    camera_call = '_configure_camera(dict(manifest["camera"]), frame_start, frame_end)'
    timeline_call = "_apply_timeline("
    assert "TIMELINE_CUE=light_flicker" in source
    assert "TIMELINE_CUE=light_energy" in source
    assert "TIMELINE_CUE=camera_push" in source
    assert "TIMELINE_CUE=character_look" in source
    assert '"character_look": _apply_character_look' in source
    assert source.index(camera_call) < source.rindex(timeline_call)
