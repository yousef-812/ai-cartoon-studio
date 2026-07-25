import json
from pathlib import Path

from packages.characters.models import CharacterCreate
from packages.series.models import LocationCreate, SeriesCreate
from packages.stories.models import StoryGenerationRequest

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "demo" / "first-real-episode"


def _json(name: str) -> object:
    return json.loads((DEMO / name).read_text(encoding="utf-8"))


def test_first_real_episode_sources_match_production_schemas() -> None:
    series = SeriesCreate.model_validate(_json("series.json"))
    location = LocationCreate.model_validate(_json("location.json"))
    characters = [CharacterCreate.model_validate(item) for item in _json("characters.json")]
    request = StoryGenerationRequest.model_validate(_json("episode_request.json"))

    assert series.primary_language == "ar"
    assert location.name == "الورشة الرئيسية"
    assert {character.name for character in characters} == {"عمر", "نادر"}
    assert all(character.voice_profile.voice_id for character in characters)
    assert request.target_duration_seconds == 40
    assert any("exactly 10 short shots" in item for item in request.constraints)
    assert any("at most one speaking character" in item for item in request.constraints)


def test_first_real_episode_model_manifest_is_complete() -> None:
    manifest = _json("model-stack.json")
    assert isinstance(manifest, dict)
    stages = {item["stage"] for item in manifest["models"]}
    assert {
        "story-script-direction",
        "images",
        "image-to-video",
        "voice",
        "lip-sync",
        "ambience-effects-music",
    }.issubset(stages)
    assert manifest["test_acceptance"]
