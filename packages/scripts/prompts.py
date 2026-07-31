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
        "cold_open": "short string",
        "scenes": [
            {
                "number": 1,
                "title": "short string",
                "slugline": "INT./EXT. LOCATION - TIME",
                "location": "registered or story location",
                "time_of_day": "string",
                "characters": ["exact registered character name"],
                "objective": "one concise sentence",
                "conflict": "one concise sentence",
                "start_state": "one concise sentence",
                "end_state": "one concise sentence",
                "action_lines": ["one or two short present-tense visible actions"],
                "dialogue": [
                    {
                        "order": 1,
                        "speaker": "exact registered character name",
                        "text": "one short spoken sentence",
                        "emotion": "specific playable emotion",
                        "delivery": "short performance direction",
                        "action_before": "optional short visible action",
                        "action_after": "optional short visible action",
                        "pause_after_ms": 200,
                        "estimated_duration_seconds": 2.5,
                    }
                ],
                "estimated_duration_seconds": example_scene_duration,
            }
        ],
        "closing_beat": "short string",
        "continuity_updates": ["short string"],
        "production_notes": ["short string"],
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
                "the exact target duration, and requested language. For technical episodes of 60 seconds "
                "or less, use exactly three scenes, one or two short action lines per scene, concise field "
                "values, and only dialogue that fits the directed duration. Avoid explanations, repeated "
                "notes, and long prose. Return one complete valid JSON object only, without markdown. "
                f"The exact output shape is: {json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(context, ensure_ascii=False, indent=2)),
    ]
