from packages.agents.director_agent import DirectorAgent


def test_director_deduplicates_dialogue_orders_without_mutating_provider_payload() -> None:
    payload = {
        "scenes": [
            {
                "scene_number": 1,
                "shots": [
                    {"dialogue_line_orders": [1]},
                    {"dialogue_line_orders": [1, 2]},
                    {"dialogue_line_orders": [2]},
                ],
            },
            {
                "scene_number": 2,
                "shots": [
                    {"dialogue_line_orders": [1]},
                ],
            },
        ]
    }

    repaired = DirectorAgent._deduplicate_dialogue_assignments(payload)

    assert payload["scenes"][0]["shots"][1]["dialogue_line_orders"] == [1, 2]
    assert repaired["scenes"][0]["shots"][0]["dialogue_line_orders"] == [1]
    assert repaired["scenes"][0]["shots"][1]["dialogue_line_orders"] == [2]
    assert repaired["scenes"][0]["shots"][2]["dialogue_line_orders"] == []
    assert repaired["scenes"][1]["shots"][0]["dialogue_line_orders"] == [1]
