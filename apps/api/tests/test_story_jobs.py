from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import stories
from app.main import app


def _series_payload(name: str) -> dict[str, object]:
    return {
        "name": name,
        "logline": "Two friends protect a floating city powered by imagination.",
        "synopsis": "An original serialized family adventure.",
        "genre": "adventure comedy",
        "target_audience": "family 8+",
        "primary_language": "en",
        "visual_style": {"art_direction": "Stylized cinematic 2D animation."},
        "rules": {"world_rules": ["Magic always has a visible cost."]},
    }


def test_story_job_is_persisted_and_queued(monkeypatch) -> None:
    queued: list[str] = []
    monkeypatch.setattr(stories.generate_story_job, "delay", queued.append)

    with TestClient(app) as client:
        series_response = client.post(
            "/api/v1/series",
            json=_series_payload(f"Story Jobs {uuid4()}"),
        )
        assert series_response.status_code == 201
        series_id = series_response.json()["id"]

        create_response = client.post(
            f"/api/v1/series/{series_id}/story-jobs",
            json={
                "premise": "A hidden station starts broadcasting tomorrow's mistakes.",
                "target_duration_seconds": 300,
                "tone": "mysterious, funny, and family friendly",
            },
        )
        assert create_response.status_code == 202
        job = create_response.json()

        list_response = client.get(f"/api/v1/series/{series_id}/story-jobs")
        get_response = client.get(f"/api/v1/story-jobs/{job['id']}")

    assert job["status"] == "queued"
    assert queued == [job["id"]]
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == job["id"]
    assert get_response.status_code == 200
