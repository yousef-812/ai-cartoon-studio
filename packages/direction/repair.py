from __future__ import annotations

from copy import deepcopy
from typing import Any

from packages.characters.models import CharacterRead
from packages.direction.models import DirectionGenerationRequest
from packages.direction.planning import allocate_shots, constrained_shot_duration
from packages.scripts.models import EpisodeScript, ScriptScene


def _text(value: Any, fallback: str, *, minimum: int = 2) -> str:
    if isinstance(value, str) and len(value.strip()) >= minimum:
        return value.strip()
    return fallback


def _text_list(value: Any, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        cleaned = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if cleaned:
            return cleaned
    return fallback[:]


def _select_evenly(items: list[tuple[int, dict[str, Any]]], count: int) -> list[tuple[int, dict[str, Any]]]:
    if count <= 0:
        return []
    if len(items) <= count:
        return items[:]
    if count == 1:
        return [items[-1]]

    selected_indexes: list[int] = []
    for position in range(count):
        index = round(position * (len(items) - 1) / (count - 1))
        if index not in selected_indexes:
            selected_indexes.append(index)
    for index in range(len(items)):
        if len(selected_indexes) >= count:
            break
        if index not in selected_indexes:
            selected_indexes.append(index)
    return [items[index] for index in sorted(selected_indexes[:count])]


def _default_shot(
    scene: ScriptScene,
    local_number: int,
    duration: float,
    registered_names: set[str],
) -> dict[str, Any]:
    scene_characters = [name for name in scene.characters if name in registered_names]
    action = (
        scene.action_lines[(local_number - 1) % len(scene.action_lines)]
        if scene.action_lines
        else f"تستمر الحركة المرئية بوضوح داخل {scene.location}."
    )
    shot_sizes = ("medium shot", "close-up reaction", "wide shot")
    return {
        "number": local_number,
        "scene_number": scene.number,
        "duration_seconds": duration,
        "shot_size": shot_sizes[(local_number - 1) % len(shot_sizes)],
        "camera_angle": "eye level",
        "camera_movement": "locked-off with minimal readable motion",
        "composition": "Clear composition with readable faces, simple silhouettes, and stable screen direction.",
        "location": scene.location,
        "characters": scene_characters,
        "action": action,
        "emotion": "focused anticipation",
        "dialogue_line_orders": [],
        "visual_prompt": (
            f"Stylized cinematic 3D animation in {scene.location}, readable faces, "
            "simple motion, approved wardrobe and prop continuity."
        ),
        "animation_notes": ["Use one simple readable action and preserve continuity."],
        "continuity_requirements": [
            "Preserve approved wardrobe, props, lighting, and screen direction."
        ],
        "transition": "cut",
    }


def _sanitize_shot(
    raw: dict[str, Any],
    scene: ScriptScene,
    local_number: int,
    duration: float,
    registered_names: set[str],
) -> dict[str, Any]:
    shot = _default_shot(scene, local_number, duration, registered_names)
    shot.update(deepcopy(raw))

    valid_characters = []
    raw_characters = shot.get("characters")
    if isinstance(raw_characters, list):
        valid_characters = [
            name for name in raw_characters if isinstance(name, str) and name in registered_names
        ]
    if not valid_characters:
        valid_characters = [name for name in scene.characters if name in registered_names]

    shot["number"] = local_number
    shot["scene_number"] = scene.number
    shot["duration_seconds"] = duration
    shot["shot_size"] = _text(shot.get("shot_size"), "medium shot")
    shot["camera_angle"] = _text(shot.get("camera_angle"), "eye level")
    shot["camera_movement"] = _text(
        shot.get("camera_movement"),
        "locked-off with minimal readable motion",
    )
    shot["composition"] = _text(
        shot.get("composition"),
        "Clear composition with readable faces and stable screen direction.",
        minimum=5,
    )
    shot["location"] = scene.location
    shot["characters"] = valid_characters
    shot["action"] = _text(
        shot.get("action"),
        scene.action_lines[0] if scene.action_lines else "تستمر الحركة المرئية بوضوح.",
        minimum=3,
    )
    shot["emotion"] = _text(shot.get("emotion"), "focused anticipation")
    shot["visual_prompt"] = _text(
        shot.get("visual_prompt"),
        f"Stylized cinematic 3D animation in {scene.location} with readable faces and simple motion.",
        minimum=10,
    )
    shot["animation_notes"] = _text_list(
        shot.get("animation_notes"),
        ["Use one simple readable action and preserve continuity."],
    )
    shot["continuity_requirements"] = _text_list(
        shot.get("continuity_requirements"),
        ["Preserve approved wardrobe, props, lighting, and screen direction."],
    )
    shot["transition"] = _text(shot.get("transition"), "cut")
    return shot


def reconcile_constrained_direction(
    payload: dict[str, Any],
    script: EpisodeScript,
    characters: list[CharacterRead],
    request: DirectionGenerationRequest,
) -> dict[str, Any]:
    """Make an exact-count direction response structurally production-safe.

    The LLM remains responsible for visual ideas, actions, and camera choices. The
    screenplay and direction request remain the source of truth for scene count,
    dialogue coverage, shot count, numbering, and duration. Missing shots are
    completed with simple silent continuity shots derived from the same scene;
    excess non-dialogue shots are sampled while every dialogue shot is preserved.
    """

    counts = allocate_shots(script, request)
    duration = constrained_shot_duration(script, request)
    if counts is None or duration is None:
        return deepcopy(payload)

    if request.max_dialogue_lines_per_shot == 0 and any(scene.dialogue for scene in script.scenes):
        raise ValueError("The screenplay contains dialogue but the direction request allows none")

    registered_names = {character.name for character in characters}
    source = deepcopy(payload) if isinstance(payload, dict) else {}
    source_scenes = source.get("scenes")
    if not isinstance(source_scenes, list):
        source_scenes = []

    repaired_scenes: list[dict[str, Any]] = []
    for scene_index, (script_scene, desired_count) in enumerate(
        zip(script.scenes, counts, strict=True)
    ):
        source_scene = (
            source_scenes[scene_index]
            if scene_index < len(source_scenes) and isinstance(source_scenes[scene_index], dict)
            else {}
        )
        raw_shots = source_scene.get("shots")
        if not isinstance(raw_shots, list):
            raw_shots = []

        valid_orders = {line.order for line in script_scene.dialogue}
        seen_orders: set[int] = set()
        indexed_shots: list[tuple[int, dict[str, Any]]] = []
        for raw_index, raw_shot in enumerate(raw_shots):
            if not isinstance(raw_shot, dict):
                continue
            shot = _sanitize_shot(
                raw_shot,
                script_scene,
                raw_index + 1,
                duration,
                registered_names,
            )
            selected_order: int | None = None
            orders = raw_shot.get("dialogue_line_orders")
            if isinstance(orders, list):
                for order in orders:
                    if isinstance(order, int) and order in valid_orders and order not in seen_orders:
                        selected_order = order
                        seen_orders.add(order)
                        break
            shot["dialogue_line_orders"] = [] if selected_order is None else [selected_order]
            indexed_shots.append((raw_index, shot))

        dialogue_shots = [item for item in indexed_shots if item[1]["dialogue_line_orders"]]
        silent_shots = [item for item in indexed_shots if not item[1]["dialogue_line_orders"]]
        silent_needed = desired_count - len(dialogue_shots)
        selected = dialogue_shots + _select_evenly(silent_shots, silent_needed)
        selected.sort(key=lambda item: item[0])
        shots = [item[1] for item in selected]

        while len(shots) < desired_count:
            shots.append(
                _default_shot(
                    script_scene,
                    len(shots) + 1,
                    duration,
                    registered_names,
                )
            )

        if len(shots) > desired_count:
            shots = shots[:desired_count]

        covered_orders = {
            order
            for shot in shots
            for order in shot.get("dialogue_line_orders", [])
            if isinstance(order, int)
        }
        missing_lines = [line for line in script_scene.dialogue if line.order not in covered_orders]
        for line in missing_lines:
            target_shot = next(
                (shot for shot in shots if not shot.get("dialogue_line_orders")),
                None,
            )
            if target_shot is None:
                raise ValueError(
                    f"Scene {script_scene.number} has too many dialogue lines for its allocated shots"
                )
            target_shot["dialogue_line_orders"] = [line.order]

        speakers = {line.order: line.speaker for line in script_scene.dialogue}
        for local_number, shot in enumerate(shots, start=1):
            shot["number"] = local_number
            shot["scene_number"] = script_scene.number
            shot["duration_seconds"] = duration
            orders = shot.get("dialogue_line_orders", [])
            if orders:
                speaker = speakers[orders[0]]
                shot["characters"] = [speaker] + [
                    name for name in shot.get("characters", []) if name != speaker
                ]

        scene_total = round(desired_count * duration, 3)
        repaired_scenes.append(
            {
                "scene_number": script_scene.number,
                "title": _text(source_scene.get("title"), script_scene.title),
                "estimated_duration_seconds": scene_total,
                "shots": shots,
            }
        )

    total = round(sum(scene["estimated_duration_seconds"] for scene in repaired_scenes), 3)
    aspect_ratio = source.get("aspect_ratio")
    if not isinstance(aspect_ratio, str) or ":" not in aspect_ratio:
        aspect_ratio = "16:9"

    return {
        "title": _text(source.get("title"), script.title),
        "aspect_ratio": aspect_ratio,
        "total_estimated_duration_seconds": total,
        "scenes": repaired_scenes,
        "global_visual_notes": _text_list(
            source.get("global_visual_notes"),
            ["Preserve the approved visual identity across every shot."],
        ),
        "continuity_notes": _text_list(
            source.get("continuity_notes"),
            ["Maintain wardrobe, props, lighting, and screen direction."],
        ),
        "production_risks": _text_list(
            source.get("production_risks"),
            ["Keep motion simple enough for the selected animation workflow."],
        ),
    }
