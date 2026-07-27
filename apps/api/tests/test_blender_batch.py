from pathlib import Path

from packages.blender.batch import build_episode_manifests
from packages.blender.models import BlenderSceneRegistry
from packages.direction.models import EpisodeDirection
from packages.scripts.models import EpisodeScript

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "demo" / "first-real-episode"


def test_approved_direction_builds_scene_scoped_blender_manifests() -> None:
    direction = EpisodeDirection.model_validate_json(
        (DEMO / "approved" / "direction.json").read_text(encoding="utf-8")
    )
    screenplay = EpisodeScript.model_validate_json(
        (DEMO / "approved" / "screenplay.json").read_text(encoding="utf-8")
    )
    registry = BlenderSceneRegistry.model_validate_json(
        (DEMO / "blender" / "scene_registry.json").read_text(encoding="utf-8")
    )

    manifests = build_episode_manifests(direction, screenplay, registry)

    assert len(manifests) == 10
    assert len({manifest.shot_key for manifest in manifests}) == 10
    assert manifests[0].shot_key == "scene:1:shot:1"
    assert manifests[-1].shot_key == "scene:4:shot:3"
    assert sum(manifest.render.duration_seconds for manifest in manifests) == 40.0

    first_scene_dialogue = manifests[0].characters[0].dialogue
    second_scene_dialogue = manifests[2].characters[0].dialogue
    assert first_scene_dialogue is not None
    assert second_scene_dialogue is not None
    assert first_scene_dialogue.text == "انطفأ الضوء!"
    assert second_scene_dialogue.text == "البطارية سليمة."

    assert all(not manifest.props for manifest in manifests)


def test_batch_uses_existing_scene_line_audio_files(tmp_path: Path) -> None:
    direction = EpisodeDirection.model_validate_json(
        (DEMO / "approved" / "direction.json").read_text(encoding="utf-8")
    )
    screenplay = EpisodeScript.model_validate_json(
        (DEMO / "approved" / "screenplay.json").read_text(encoding="utf-8")
    )
    registry = BlenderSceneRegistry.model_validate_json(
        (DEMO / "blender" / "scene_registry.json").read_text(encoding="utf-8")
    )
    audio = tmp_path / "scene_01_line_01.wav"
    audio.write_bytes(b"RIFF")

    manifests = build_episode_manifests(
        direction,
        screenplay,
        registry,
        audio_root=tmp_path,
    )

    dialogue = manifests[0].characters[0].dialogue
    assert dialogue is not None
    assert dialogue.audio_path == str(audio.resolve())
