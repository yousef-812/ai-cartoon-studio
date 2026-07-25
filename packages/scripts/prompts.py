import json

from packages.characters.models import CharacterRead
from packages.llm.models import LLMMessage
from packages.scripts.models import ScriptGenerationRequest
from packages.series.models import LocationRead, SeriesRead
from packages.stories.models import EpisodeStory


def build_script_messages(
    series: SeriesRead,
    characters: list[CharacterRead],
    locations: list[LocationRead],
    story: EpisodeStory,
    request: ScriptGenerationRequest,
) -> list[LLMMessage]:
    target_duration = request.target_duration_seconds or sum(
        scene.estimated_duration_seconds for scene in story.scenes
    )
    example_scene_duration = max(5, round(target_duration / max(1, len(story.scenes))))
    schema = {
        "title": "string",
        "language": "series primary language",
        "target_duration_seconds": target_duration,
        "total_estimated_duration_seconds": target_duration,
        "cold_open": "string",
        "scenes": [
            {
                "number": 1,
                "title": "string",
                "slugline": "INT./EXT. LOCATION - TIME",
                "location": "registered or story location",
                "time_of_day": "string",
                "characters": ["exact registered character name"],
                "objective": "string",
                "conflict": "string",
                "start_state": "string",
                "end_state": "string",
                "action_lines": ["present-tense visible action"],
                "dialogue": [
                    {
                        "order": 1,
                        "speaker": "exact registered character name",
                        "text": "spoken line only",
                        "emotion": "specific playable emotion",
                        "delivery": "performance direction",
                        "action_before": "optional visible action",
                        "action_after": "optional visible action",
                        "pause_after_ms": 200,
                        "estimated_duration_seconds": 2.5,
                    }
                ],
                "estimated_duration_seconds": example_scene_duration,
            }
        ],
        "closing_beat": "string",
        "continuity_updates": ["string"],
        "production_notes": ["string"],
    }
    context = {
        "series": series.model_dump(mode="json"),
        "characters": [character.model_dump(mode="json") for character in characters],
        "locations": [location.model_dump(mode="json") for location in locations],
        "approved_story": story.model_dump(mode="json"),
        "script_request": request.model_dump(mode="json"),
    }
    return [
        LLMMessage(
            role="system",
            content=(
                "You are the lead animation screenwriter. Convert the approved episode story into "
                "a production-ready screenplay without changing its core plot, ending, world rules, "
                "or character identities. Dialogue must sound different for each character and use "
                "only exact registered character names as speakers. Keep action visible and playable. "
                "Do not add camera shots; directing is a later stage. Respect every request constraint, "
                "the exact target duration, and requested language. Return one valid JSON object only, "
                "without markdown. "
                f"The exact output shape is: {json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(context, ensure_ascii=False, indent=2)),
    ]
