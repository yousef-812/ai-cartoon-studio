from packages.agents.director_agent import DirectorAgent
from packages.direction.models import DirectedScene


def _shot(number: int, scene_number: int, duration: float) -> dict[str, object]:
    return {
        "number": number,
        "scene_number": scene_number,
        "duration_seconds": duration,
        "shot_size": "medium",
        "camera_angle": "eye level",
        "camera_movement": "locked",
        "composition": "Readable workshop composition with clear foreground action.",
        "location": "الورشة الرئيسية",
        "characters": ["عمر"],
        "action": "عمر يفحص المصباح بهدوء.",
        "emotion": "تركيز",
        "dialogue_line_orders": [],
        "visual_prompt": "Stylized cinematic workshop scene with readable character silhouette.",
        "animation_notes": ["Keep motion minimal."],
        "continuity_requirements": ["Preserve Omar's teal jacket and glasses."],
        "transition": "cut",
    }


def test_director_reconciles_scene_and_episode_totals_from_shots() -> None:
    payload = {
        "total_estimated_duration_seconds": 40.0,
        "scenes": [
            {
                "scene_number": 1,
                "estimated_duration_seconds": 20.0,
                "shots": [_shot(1, 1, 4.0), _shot(2, 1, 4.0)],
            },
            {
                "scene_number": 2,
                "estimated_duration_seconds": 20.0,
                "shots": [_shot(1, 2, 3.5), _shot(2, 2, 3.5)],
            },
            {
                "scene_number": 3,
                "estimated_duration_seconds": 20.0,
                "shots": [
                    _shot(1, 3, 4.0),
                    _shot(2, 3, 4.0),
                    _shot(3, 3, 4.0),
                ],
            },
            {
                "scene_number": 4,
                "estimated_duration_seconds": 20.0,
                "shots": [
                    _shot(1, 4, 3.5),
                    _shot(2, 4, 3.5),
                    _shot(3, 4, 3.5),
                ],
            },
        ],
    }

    repaired = DirectorAgent._reconcile_duration_totals(payload)

    assert payload["scenes"][0]["estimated_duration_seconds"] == 20.0
    assert [scene["estimated_duration_seconds"] for scene in repaired["scenes"]] == [
        8.0,
        7.0,
        12.0,
        10.5,
    ]
    assert repaired["total_estimated_duration_seconds"] == 37.5


def test_directed_scene_allows_one_short_shot() -> None:
    scene = DirectedScene.model_validate(
        {
            "scene_number": 1,
            "title": "لمحة سريعة",
            "estimated_duration_seconds": 4.0,
            "shots": [_shot(1, 1, 4.0)],
        }
    )

    assert scene.estimated_duration_seconds == 4.0
    assert len(scene.shots) == 1
