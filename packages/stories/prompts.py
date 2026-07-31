import json

from packages.characters.models import CharacterRead
from packages.llm.models import LLMMessage
from packages.series.models import LocationRead, SeriesRead
from packages.stories.models import StoryGenerationRequest


def build_story_messages(
    series: SeriesRead,
    characters: list[CharacterRead],
    locations: list[LocationRead],
    request: StoryGenerationRequest,
) -> list[LLMMessage]:
    example_scene_duration = max(5, round(request.target_duration_seconds / 3))
    schema = {
        "title": "string",
        "logline": "string",
        "theme": "string",
        "hook": "string",
        "synopsis": "string",
        "beats": [{"title": "string", "summary": "string", "purpose": "string"}],
        "scenes": [
            {
                "number": 1,
                "title": "string",
                "location": "exact registered location name",
                "characters": ["exact registered character name"],
                "objective": "string",
                "conflict": "string",
                "outcome": "string",
                "estimated_duration_seconds": example_scene_duration,
            }
        ],
        "ending": "string",
        "continuity_updates": ["string"],
        "safety_notes": ["string"],
    }
    context = {
        "series": series.model_dump(mode="json"),
        "characters": [character.model_dump(mode="json") for character in characters],
        "locations": [location.model_dump(mode="json") for location in locations],
        "episode_request": request.model_dump(mode="json"),
    }
    return [
        LLMMessage(
            role="system",
            content=(
                "You are the head story editor for an original animated series. "
                "Protect character identity, world rules, continuity, age suitability, and the "
                "requested language. Use only exact registered character and location names. "
                "Respect every episode constraint and keep the sum of scene durations close to "
                f"the exact {request.target_duration_seconds}-second target. Produce a genuinely "
                "different episode, not a template rewrite. Return one valid JSON object only, "
                "with no markdown or commentary. "
                f"The exact output shape is: {json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
        LLMMessage(
            role="user",
            content=json.dumps(context, ensure_ascii=False, indent=2),
        ),
    ]
