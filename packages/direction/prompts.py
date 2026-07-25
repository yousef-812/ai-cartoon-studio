import json

from packages.characters.models import CharacterRead
from packages.direction.models import DirectionGenerationRequest
from packages.llm.models import LLMMessage
from packages.scripts.models import EpisodeScript
from packages.series.models import LocationRead, SeriesRead


def build_direction_messages(
    series: SeriesRead,
    characters: list[CharacterRead],
    locations: list[LocationRead],
    script: EpisodeScript,
    request: DirectionGenerationRequest,
) -> list[LLMMessage]:
    first_scene_duration = script.scenes[0].estimated_duration_seconds if script.scenes else 10
    schema = {
        "title": "string",
        "aspect_ratio": "16:9",
        "total_estimated_duration_seconds": script.total_estimated_duration_seconds,
        "scenes": [
            {
                "scene_number": 1,
                "title": "string",
                "estimated_duration_seconds": first_scene_duration,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 1,
                        "duration_seconds": request.max_shot_duration_seconds,
                        "shot_size": "wide/medium/close-up/etc",
                        "camera_angle": "string",
                        "camera_movement": "string",
                        "composition": "string",
                        "location": "string",
                        "characters": ["exact registered character name"],
                        "action": "visible action",
                        "emotion": "string",
                        "dialogue_line_orders": [1],
                        "visual_prompt": "production visual prompt",
                        "animation_notes": ["string"],
                        "continuity_requirements": ["string"],
                        "transition": "cut",
                    }
                ],
            }
        ],
        "global_visual_notes": ["string"],
        "continuity_notes": ["string"],
        "production_risks": ["string"],
    }
    context = {
        "series": series.model_dump(mode="json"),
        "characters": [character.model_dump(mode="json") for character in characters],
        "locations": [location.model_dump(mode="json") for location in locations],
        "approved_screenplay": script.model_dump(mode="json"),
        "direction_request": request.model_dump(mode="json"),
    }
    return [
        LLMMessage(
            role="system",
            content=(
                "You are the director and storyboard planner for an original animated series. "
                "Convert the approved screenplay into production shots. Preserve every scene, "
                "dialogue order, character identity, location, wardrobe, continuity rule, and total "
                "timing. Use exact registered character names. Make shots visually readable, "
                "emotionally motivated, and economical enough for AI animation. Every dialogue line "
                "order must appear in an appropriate shot. Respect every direction constraint and do "
                "not exceed the requested maximum shot duration. Return one valid JSON object only, "
                "without markdown. "
                f"The exact output shape is: {json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(context, ensure_ascii=False, indent=2)),
    ]
