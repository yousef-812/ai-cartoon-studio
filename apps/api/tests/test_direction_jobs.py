from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import directions
from app.db.session import SessionLocal
from app.main import app
from app.repositories.scripts import SQLScriptJobRepository
from app.repositories.stories import SQLStoryJobRepository
from packages.scripts.models import EpisodeScript, ScriptGenerationRequest, ScriptReviewRequest
from packages.stories.models import (
    EpisodeStory,
    StoryGenerationRequest,
    StoryReviewRequest,
)


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


def _story() -> EpisodeStory:
    return EpisodeStory(
        title="The Clockwork Cloud",
        logline="A cloud engine must be repaired before the city loses balance.",
        theme="Patience makes invention responsible.",
        hook="A golden cloud freezes and starts lifting buildings.",
        synopsis=(
            "A rushed repair makes the cloud engine worse, so the team slows down and follows a "
            "careful sequence before restoring the city safely and learning a lasting lesson."
        ),
        beats=[
            {"title": "Disruption", "summary": "The cloud freezes above the market.", "purpose": "Hook"},
            {"title": "Failure", "summary": "The rushed repair overloads the engine.", "purpose": "Escalation"},
            {"title": "Repair", "summary": "The engine is repaired carefully.", "purpose": "Resolution"},
        ],
        scenes=[
            {"number": 1, "title": "Frozen Sky", "location": "Cloud Market", "objective": "Find the fault.", "conflict": "Buildings rise.", "outcome": "The engine is found.", "estimated_duration_seconds": 60},
            {"number": 2, "title": "Rushed Repair", "location": "Engine Room", "objective": "Restart it.", "conflict": "The shortcut fails.", "outcome": "The plan changes.", "estimated_duration_seconds": 60},
            {"number": 3, "title": "Careful Solution", "location": "Engine Room", "objective": "Repair it.", "conflict": "Time is short.", "outcome": "The city stabilizes.", "estimated_duration_seconds": 60},
        ],
        ending="The control is labeled so the lesson remains visible in future episodes.",
    )


def _script() -> EpisodeScript:
    scenes = []
    for number, title, location in [
        (1, "Frozen Sky", "Cloud Market"),
        (2, "Rushed Repair", "Engine Room"),
        (3, "Careful Solution", "Engine Room"),
    ]:
        scenes.append(
            {
                "number": number,
                "title": title,
                "slugline": f"INT. {location.upper()} - DAY",
                "location": location,
                "time_of_day": "day",
                "characters": [],
                "objective": "Solve the immediate problem.",
                "conflict": "The failure escalates while time runs short.",
                "start_state": "The team begins uncertain but determined.",
                "end_state": "The team gains clarity and advances the solution.",
                "action_lines": ["The mechanism is studied carefully."],
                "dialogue": [],
                "estimated_duration_seconds": 60,
            }
        )
    return EpisodeScript(
        title="The Clockwork Cloud",
        language="en",
        target_duration_seconds=180,
        total_estimated_duration_seconds=180,
        cold_open="A frozen cloud pulls the market upward without warning.",
        scenes=scenes,
        closing_beat="The repaired engine settles into a warm and steady rhythm.",
    )


def test_direction_job_requires_approved_screenplay(monkeypatch) -> None:
    queued: list[str] = []
    monkeypatch.setattr(directions.generate_direction_job, "delay", queued.append)

    with TestClient(app) as client:
        series_response = client.post(
            "/api/v1/series",
            json=_series_payload(f"Direction Jobs {uuid4()}"),
        )
        assert series_response.status_code == 201
        series_id = series_response.json()["id"]

        session = SessionLocal()
        try:
            story_repository = SQLStoryJobRepository(session)
            story_job = story_repository.create(
                series_id,
                StoryGenerationRequest(
                    premise="A cloud engine freezes during the busiest market day.",
                    target_duration_seconds=180,
                ),
                "local",
                "fake-7b",
            )
            story_repository.complete(story_job.id, _story())
            story_repository.review(
                story_job.id,
                StoryReviewRequest(decision="approved", notes="Approved."),
            )

            script_repository = SQLScriptJobRepository(session)
            script_job = script_repository.create(
                series_id,
                story_job.id,
                ScriptGenerationRequest(target_duration_seconds=180),
                "local",
                "fake-7b",
            )
            script_repository.complete(script_job.id, _script())
        finally:
            session.close()

        blocked = client.post(
            f"/api/v1/script-jobs/{script_job.id}/direction-jobs",
            json={"max_shot_duration_seconds": 30},
        )
        assert blocked.status_code == 409

        review_response = client.post(
            f"/api/v1/script-jobs/{script_job.id}/review",
            json={"decision": "approved", "notes": "Approved for directing."},
        )
        assert review_response.status_code == 200

        create_response = client.post(
            f"/api/v1/script-jobs/{script_job.id}/direction-jobs",
            json={"max_shot_duration_seconds": 30},
        )
        assert create_response.status_code == 202
        direction_job = create_response.json()

        list_response = client.get(f"/api/v1/series/{series_id}/direction-jobs")

    assert queued == [direction_job["id"]]
    assert direction_job["status"] == "queued"
    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == direction_job["id"]
