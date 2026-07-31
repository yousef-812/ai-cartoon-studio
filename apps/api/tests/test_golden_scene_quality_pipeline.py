import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_workshop_build_runs_quality_upgrade_before_validation():
    script = source("scripts/build_demo_blender_scene.sh")
    upgrade = "--python workers/blender/upgrade_workshop_quality.py"
    validate = "--python workers/blender/validate_scene.py"
    assert upgrade in script
    assert validate in script
    assert script.index(upgrade) < script.index(validate)


def test_quality_scene_keeps_registered_character_contracts():
    registry = json.loads(source("demo/first-real-episode/blender/scene_registry.json"))
    assert registry["characters"]["عمر"]["rig_object"] == "Omar_Rig"
    assert registry["characters"]["نادر"]["rig_object"] == "Nader_Rig"
    assert registry["characters"]["عمر"]["actions"]["react_light_out"] == "Omar_ReactLightOut"
    assert registry["characters"]["نادر"]["actions"]["concern_settle"] == "Nader_ConcernSettle"


def test_authored_performance_replaces_generic_talk_actions():
    script = source("scripts/apply_golden_scene_performance.py")
    assert '"عمر": "Omar_ReactLightOut"' in script
    assert '"نادر": "Nader_Surprised"' in script
    assert '"نادر": "Nader_Worried"' in script
    assert '"عمر": 0.82' in script
    assert '"نادر": 1.42' in script


def test_quality_runner_rebuilds_scene_mixes_sound_and_writes_review():
    runner = source("scripts/run_demo_voiced_blender_preview.sh")
    assert 'QUALITY_SCENE_REBUILD="${QUALITY_SCENE_REBUILD:-1}"' in runner
    assert 'GOLDEN_SOUND="${GOLDEN_SOUND:-1}"' in runner
    assert "scripts/generate_golden_scene_sound.py" in runner
    assert "scripts/mix_golden_scene_audio.py" in runner
    assert "scripts/build_golden_scene_review.py" in runner


def test_review_gate_never_auto_approves_a_render():
    review = source("scripts/build_golden_scene_review.py")
    assert '"production_approved": False' in review
    assert '"promotion_blocked": True' in review
    assert '"decision": "pending"' in review
