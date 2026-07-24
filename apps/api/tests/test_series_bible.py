from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def series_payload(name: str) -> dict[str, object]:
    return {
        "name": name,
        "logline": "Two unlikely friends protect a city powered by imagination.",
        "synopsis": "A serialized family adventure with permanent characters and locations.",
        "genre": "adventure comedy",
        "target_audience": "family 8+",
        "primary_language": "en",
        "visual_style": {
            "art_direction": "Stylized cinematic 2D animation with expressive silhouettes.",
            "medium": "2d animation",
            "palette": ["#E9B44C", "#253D5B", "#F4F1DE"],
            "line_style": "clean tapered lines",
            "lighting": "warm cinematic lighting",
            "aspect_ratio": "16:9",
        },
        "rules": {
            "world_rules": ["Magic always has a visible cost."],
            "prohibited_topics": ["graphic violence"],
            "continuity_notes": ["The city floats above a permanent cloud layer."],
        },
    }


def test_create_series_and_character() -> None:
    unique_name = f"Skykeepers {uuid4()}"

    with TestClient(app) as client:
        series_response = client.post("/api/v1/series", json=series_payload(unique_name))
        assert series_response.status_code == 201
        series = series_response.json()

        character_response = client.post(
            f"/api/v1/series/{series['id']}/characters",
            json={
                "name": "Mira",
                "role": "protagonist",
                "age_range": "12-14",
                "description": "A curious young inventor who acts before she finishes planning.",
                "personality_traits": ["curious", "brave", "impatient"],
                "visual_identity": {
                    "reference_prompt": (
                        "Mira is a stylized teenage inventor with round goggles and a short jacket."
                    ),
                    "body_shape": "small athletic silhouette",
                    "face": "round face with large brown eyes",
                    "hair": "dark curly bob",
                    "palette": ["amber", "navy", "cream"],
                    "signature_features": ["round goggles", "tool belt"],
                },
                "wardrobe": {"default": "amber jacket, navy trousers, cream boots"},
                "speaking_style": "Fast, optimistic, and full of technical metaphors.",
                "voice_profile": {
                    "language": "en",
                    "description": "Warm youthful voice with energetic delivery.",
                },
            },
        )
        assert character_response.status_code == 201
        character = character_response.json()

        list_response = client.get(f"/api/v1/series/{series['id']}/characters")

    assert series["slug"].startswith("skykeepers-")
    assert character["series_id"] == series["id"]
    assert character["visual_identity"]["signature_features"] == ["round goggles", "tool belt"]
    assert list_response.status_code == 200
    assert any(item["id"] == character["id"] for item in list_response.json())


def test_duplicate_series_slug_returns_conflict() -> None:
    unique_name = f"Duplicate Test {uuid4()}"
    payload = series_payload(unique_name)
    payload["slug"] = f"duplicate-{uuid4()}"

    with TestClient(app) as client:
        first = client.post("/api/v1/series", json=payload)
        second = client.post("/api/v1/series", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
