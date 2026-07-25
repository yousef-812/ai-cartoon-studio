from packages.agents.director_agent import DirectorAgent
from packages.scripts.models import EpisodeScript


def _script() -> EpisodeScript:
    scenes = []
    for number in range(1, 4):
        scenes.append(
            {
                "number": number,
                "title": f"Scene {number}",
                "slugline": "INT. WORKSHOP - NIGHT",
                "location": "Main Workshop",
                "time_of_day": "night",
                "characters": ["Omar", "Nader"],
                "objective": "Complete the emergency lamp safely.",
                "conflict": "The storm keeps cutting the workshop power.",
                "start_state": "The repair is incomplete and the room is dark.",
                "end_state": "The team advances the repair by one clear step.",
                "action_lines": ["The friends work at the central bench."],
                "dialogue": [],
                "estimated_duration_seconds": 10,
            }
        )
    return EpisodeScript(
        title="Emergency Lamp",
        language="ar",
        target_duration_seconds=30,
        total_estimated_duration_seconds=30,
        cold_open="A storm suddenly cuts all power inside the workshop.",
        scenes=scenes,
        closing_beat="The repaired lamp fills the workshop with warm light.",
    )


def test_director_normalizes_scene_and_local_shot_numbers_without_mutating_payload() -> None:
    payload = {
        "scenes": [
            {
                "scene_number": 7,
                "shots": [
                    {"number": 1, "scene_number": 7},
                    {"number": 2, "scene_number": 7},
                ],
            },
            {
                "scene_number": 8,
                "shots": [
                    {"number": 3, "scene_number": 8},
                    {"number": 4, "scene_number": 8},
                    {"number": 5, "scene_number": 8},
                ],
            },
            {
                "scene_number": 9,
                "shots": [
                    {"number": 6, "scene_number": 9},
                ],
            },
        ]
    }

    repaired = DirectorAgent._normalize_scene_and_shot_numbering(payload, _script())

    assert payload["scenes"][1]["shots"][0]["number"] == 3
    assert [scene["scene_number"] for scene in repaired["scenes"]] == [1, 2, 3]
    assert [shot["number"] for shot in repaired["scenes"][0]["shots"]] == [1, 2]
    assert [shot["number"] for shot in repaired["scenes"][1]["shots"]] == [1, 2, 3]
    assert [shot["scene_number"] for shot in repaired["scenes"][1]["shots"]] == [2, 2, 2]
    assert repaired["scenes"][2]["shots"][0] == {"number": 1, "scene_number": 3}
