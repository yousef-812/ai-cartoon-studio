from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import scripts, stories
from app.db.session import SessionLocal
from app.main import app
from app.repositories.stories import SQLStoryJobRepository
from packages.stories.models import EpisodeStory


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


def _completed_story() -> EpisodeStory:
    return EpisodeStory(
        title="The Clockwork Cloud",
        logline="Mira must repair a cloud engine before her floating city loses balance.",
        theme="Patience makes invention responsible.",
        hook="A golden cloud freezes above the city and starts lifting buildings.",
        synopsis=(
            "Mira rushes to repair the cloud engine, makes the failure worse, then learns to "
            "slow down and follow a careful sequence before restoring the city safely."
        ),
        beats=[
            {"title": "Disruption", "summary": "The cloud freezes above the market.", "purpose": "Hook"},
            {"title": "Failure", "summary": "A rushed repair overloads the engine.", "purpose": "Escalation"},
            {"title": "Repair", "summary": "Mira repairs it patiently.", "purpose": "Resolution"},
        ],
        scenes=[
            {"number": 1, "title": "Frozen Sky", "location": "Cloud Market", "characters": [], "objective": "Find the fault.", "conflict": "Buildings rise.", "outcome": "The engine is located.", "estimated_duration_seconds": 60},
            {"number": 2, "title": "Rushed Repair", "location": "Cloud Engine Room", "characters": [], "objective": "Restart it.", "conflict": "The shortcut fails.", "outcome": "The approach changes.", "estimated_duration_seconds": 60},
            {"number": 3, "title": "Careful Solution", "location": "Cloud Engine Room", "characters": [], "objective": "Repair it carefully.", "conflict": "Time is short.", "outcome": "The city stabilizes.", "estimated_duration_seconds": 60},
        ],
        ending="The repaired control is labeled so the team remembers to listen before launching.",
    )


def test_script_job_requires_approved_story_and_is_persisted(monkeypatch) -> None:
    story_queue: list[str] = []
    script_queue: list[str] = []
    monkeypatch.setattr(stories.generate_story_job, "delay", story_queue.append)
    monkeypatch.setattr(scripts.generate_script_job, "delay", script_queue.append)

    with TestClient(app) as client:
        series_response = client.post(
            "/api/v1/series",
            json=_series_payload(f"Script Jobs {uuid4()}"),
        )
        assert series_response.status_code == 201
        series_id = series_response.json()["id"]

        story_response = client.post(
            f"/api/v1/series/{series_id}/story-jobs",
            json={
                "premise": "A cloud engine freezes during the busiest market day.",
                "target_duration_seconds": 180,
            },
        )
        assert story_response.status_code == 202
        story_job_id = story_response.json()["id"]

        blocked = client.post(
            f"/api/v1/story-jobs/{story_job_id}/script-jobs",
            json={},
        )
        assert blocked.status_code == 409

        session = SessionLocal()
        try:
            repository = SQLStoryJobRepository(session)
            completed = repository.complete(story_job_id, _completed_story())
            assert completed is not None
        finally:
            session.close()

        review_response = client.post(
            f"/api/v1/story-jobs/{story_job_id}/review",
            json={"decision": "approved", "notes": "Story structure approved."},
        )
        assert review_response.status_code == 200
        assert review_response.json()["review_status"] == "approved"

        create_response = client.post(
            f"/api/v1/story-jobs/{story_job_id}/script-jobs",
            json={"dialogue_style": "warm, concise, and character specific"},
        )
        assert create_response.status_code == 202
        script_job = create_response.json()

        list_response = client.get(f"/api/v1/series/{series_id}/script-jobs")
        get_response = client.get(f"/api/v1/script-jobs/{script_job['id']}")

    assert story_queue == [story_job_id]
    assert script_queue == [script_job["id"]]
    assert script_job["status"] == "queued"
    assert script_job["request"]["target_duration_seconds"] == 180
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == script_job["id"]
    assert get_response.status_code == 200
