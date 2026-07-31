import json

from packages.characters.models import CharacterRead
from packages.direction.models import DirectionGenerationRequest
from packages.direction.planning import allocate_shots, constrained_shot_duration
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
    shot_counts = allocate_shots(script, request)
    shot_duration = constrained_shot_duration(script, request)
    mandatory_layout = None
    if shot_counts is not None and shot_duration is not None:
        mandatory_layout = [
            {
                "scene_number": scene.number,
                "exact_shot_count": count,
                "local_shot_numbers": list(range(1, count + 1)),
                "duration_seconds_for_every_shot": shot_duration,
                "dialogue_orders_to_cover_exactly_once": [
                    line.order for line in scene.dialogue
                ],
            }
            for scene, count in zip(script.scenes, shot_counts, strict=True)
        ]

    first_scene_duration = (
        (shot_counts[0] * shot_duration)
        if shot_counts is not None and shot_duration is not None
        else (script.scenes[0].estimated_duration_seconds if script.scenes else 10)
    )
    schema = {
        "title": "string",
        "aspect_ratio": "16:9",
        "total_estimated_duration_seconds": (
            request.target_shot_count * shot_duration
            if request.target_shot_count is not None and shot_duration is not None
            else script.total_estimated_duration_seconds
        ),
        "scenes": [
            {
                "scene_number": 1,
                "title": "string",
                "estimated_duration_seconds": first_scene_duration,
                "shots": [
                    {
                        "number": 1,
                        "scene_number": 1,
                        "duration_seconds": (
                            shot_duration
                            if shot_duration is not None
                            else request.max_shot_duration_seconds
                        ),
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
        "mandatory_shot_layout": mandatory_layout,
    }
    target_shots = (
        f" Produce exactly {request.target_shot_count} shots in total."
        if request.target_shot_count is not None
        else ""
    )
    dialogue_limit = (
        f" Put no more than {request.max_dialogue_lines_per_shot} dialogue line orders in one shot."
        if request.max_dialogue_lines_per_shot is not None
        else ""
    )
    return [
        LLMMessage(
            role="system",
            content=(
                "You are the director and storyboard planner for an original animated series. "
                "Convert the approved screenplay into production shots. Preserve every scene, "
                "dialogue order, character identity, location, wardrobe, continuity rule, and total "
                "timing. Use exact registered character names. Make shots visually readable, "
                "emotionally motivated, and economical enough for AI animation. Every dialogue line "
                "order must appear in exactly one appropriate shot. Respect every direction constraint. "
                f"Keep every shot between {request.min_shot_duration_seconds} and "
                f"{request.max_shot_duration_seconds} seconds.{target_shots}{dialogue_limit} "
                "The mandatory_shot_layout is the structural source of truth: return exactly one "
                "directed scene for every listed scene, exactly the listed number of local shots, the "
                "listed shot numbers, and the listed duration for every shot. Do not merge, omit, or "
                "add scenes or shots. Fill each mandatory slot with concise camera, action, emotion, "
                "and visual-prompt content. Return one valid JSON object only, without markdown. "
                f"The exact output shape is: {json.dumps(schema, ensure_ascii=False)}"
            ),
        ),
        LLMMessage(role="user", content=json.dumps(context, ensure_ascii=False, indent=2)),
    ]
