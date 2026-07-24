from fastapi.testclient import TestClient

from app.main import app


def test_create_episode_plan() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/production/episodes",
            json={
                "series_id": "series-demo",
                "title": "The First Adventure",
                "premise": "Two friends discover a hidden floating city.",
                "target_duration_seconds": 240,
            },
        )

    assert response.status_code == 202
    body = response.json()
    assert body["stage"] == "concept"
    assert body["status"] == "pending_review"
