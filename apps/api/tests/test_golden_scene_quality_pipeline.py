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
