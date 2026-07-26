from pathlib import Path

from packages.blender.models import BlenderSceneRegistry, BlenderShotManifest
from packages.blender.planner import BlenderShotPlanner
from packages.blender.visemes import build_viseme_cues
from packages.direction.models import ShotPlan

ROOT = Path(__file__).resolve().parents[3]
BLENDER_DEMO = ROOT / "demo" / "first-real-episode" / "blender"


def test_demo_blender_registry_and_smoke_shot_are_valid() -> None:
    registry = BlenderSceneRegistry.model_validate_json(
        (BLENDER_DEMO / "scene_registry.json").read_text(encoding="utf-8")
    )
    shot = BlenderShotManifest.model_validate_json(
        (BLENDER_DEMO / "shot_smoke.json").read_text(encoding="utf-8")
    )

    assert registry.scene_name == "WorkshopOfLight"
    assert set(registry.characters) == {"عمر", "نادر"}
    assert shot.render.frame_end == 96
    assert [character.action_name for character in shot.characters] == [
        "Omar_Talk",
        "Nader_Listen",
    ]
    assert shot.characters[0].dialogue is not None
    assert shot.characters[0].dialogue.visemes[-1].name == "REST"


def test_viseme_fallback_is_bounded_and_monotonic() -> None:
    cues = build_viseme_cues(
        "المشكلة مش في البطارية",
        start_seconds=0.25,
        duration_seconds=3.2,
    )

    assert cues[0].time_seconds == 0.25
    assert cues[-1].time_seconds == 3.45
    assert cues[-1].name == "REST"
    assert [cue.time_seconds for cue in cues] == sorted(cue.time_seconds for cue in cues)
    assert {cue.name for cue in cues} >= {"REST", "A", "M"}


def test_blender_planner_assigns_reusable_actions_and_dialogue() -> None:
    registry = BlenderSceneRegistry.model_validate_json(
        (BLENDER_DEMO / "scene_registry.json").read_text(encoding="utf-8")
    )
    shot = ShotPlan(
        number=2,
        scene_number=1,
        duration_seconds=4.0,
        shot_size="medium two shot",
        camera_angle="eye level",
        camera_movement="locked",
        composition="Omar and Nader face each other beside the workbench.",
        location="ورشة النور",
        characters=["عمر", "نادر"],
        action="عمر يشرح بينما نادر يستمع.",
        emotion="focused reassurance",
        dialogue_line_orders=[1],
        visual_prompt="Omar and Nader in the permanent workshop environment.",
        animation_notes=["Readable hand gesture"],
        continuity_requirements=["Keep the lantern on the workbench"],
    )

    manifest = BlenderShotPlanner(registry).plan(
        shot,
        fps=24,
        dialogue_by_order={
            1: {
                "speaker": "عمر",
                "text": "المشكلة مش في البطارية.",
                "audio_path": "/tmp/omar-line.wav",
                "start_seconds": 0.3,
                "duration_seconds": 3.0,
            }
        },
    )

    assert manifest.camera.object_name == "CAM_Medium"
    assert manifest.characters[0].action_name == "Omar_Talk"
    assert manifest.characters[1].action_name == "Nader_Listen"
    assert manifest.characters[0].dialogue is not None
    assert manifest.characters[0].dialogue.audio_path == "/tmp/omar-line.wav"
    assert manifest.characters[1].dialogue is None
