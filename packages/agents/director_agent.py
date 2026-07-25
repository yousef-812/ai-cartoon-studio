from typing import Any

from pydantic import ValidationError

from packages.agents.base import ProductionAgent
from packages.characters.models import CharacterRead
from packages.direction.models import DirectionGenerationRequest, EpisodeDirection
from packages.direction.prompts import build_direction_messages
from packages.llm.errors import LLMResponseError
from packages.llm.models import LLMMessage
from packages.llm.provider import LLMProvider
from packages.scripts.models import EpisodeScript
from packages.series.models import LocationRead, SeriesRead


class DirectorAgent(ProductionAgent):
    name = "director"

    def __init__(self, provider: LLMProvider, validation_retries: int = 1) -> None:
        self.provider = provider
        self.validation_retries = validation_retries

    @staticmethod
    def _validate_plan(
        direction: EpisodeDirection,
        script: EpisodeScript,
        characters: list[CharacterRead],
        request: DirectionGenerationRequest,
    ) -> None:
        registered = {character.name for character in characters}
        all_shots = [shot for scene in direction.scenes for shot in scene.shots]
        unknown_characters = sorted(
            {
                name
                for shot in all_shots
                for name in shot.characters
                if name not in registered
            }
        )
        if unknown_characters:
            raise ValueError(f"Unknown shot characters: {', '.join(unknown_characters)}")

        if len(direction.scenes) != len(script.scenes):
            raise ValueError("The direction plan must preserve every screenplay scene")
        if request.target_shot_count is not None and len(all_shots) != request.target_shot_count:
            raise ValueError(
                f"Direction must contain exactly {request.target_shot_count} shots; "
                f"received {len(all_shots)}"
            )
        if any(
            shot.duration_seconds < request.min_shot_duration_seconds for shot in all_shots
        ):
            raise ValueError(
                f"A shot is shorter than the {request.min_shot_duration_seconds}s minimum duration"
            )
        if any(
            shot.duration_seconds > request.max_shot_duration_seconds for shot in all_shots
        ):
            raise ValueError(
                f"A shot exceeds the {request.max_shot_duration_seconds}s maximum duration"
            )
        if request.max_dialogue_lines_per_shot is not None and any(
            len(shot.dialogue_line_orders) > request.max_dialogue_lines_per_shot
            for shot in all_shots
        ):
            raise ValueError(
                "A shot exceeds the requested maximum number of dialogue lines"
            )

        for directed_scene, script_scene in zip(direction.scenes, script.scenes, strict=True):
            if directed_scene.scene_number != script_scene.number:
                raise ValueError("Directed scene numbers must match screenplay scene numbers")

            valid_lines = {line.order for line in script_scene.dialogue}
            covered_order_list = [
                order for shot in directed_scene.shots for order in shot.dialogue_line_orders
            ]
            covered_lines = set(covered_order_list)
            if covered_lines != valid_lines:
                raise ValueError(
                    f"Scene {script_scene.number} shots must cover every dialogue line by order"
                )
            if len(covered_order_list) != len(covered_lines):
                raise ValueError(
                    f"Scene {script_scene.number} assigns a dialogue line to more than one shot"
                )

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        series = SeriesRead.model_validate(context["series"])
        characters = [CharacterRead.model_validate(item) for item in context.get("characters", [])]
        locations = [LocationRead.model_validate(item) for item in context.get("locations", [])]
        script = EpisodeScript.model_validate(context["script"])
        request = DirectionGenerationRequest.model_validate(context["request"])
        messages = build_direction_messages(series, characters, locations, script, request)

        last_error: LLMResponseError | ValidationError | ValueError | None = None
        for attempt in range(self.validation_retries + 1):
            try:
                payload = await self.provider.generate_json(
                    messages,
                    temperature=0.2,
                    max_tokens=12288,
                )
                direction = EpisodeDirection.model_validate(payload)
                self._validate_plan(direction, script, characters, request)
                return direction.model_dump(mode="json")
            except (LLMResponseError, ValidationError, ValueError) as error:
                last_error = error
                if attempt < self.validation_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "The previous direction response was incomplete, invalid, or failed "
                                "validation. Return the complete JSON again with concise shot fields, "
                                "no redundant prose, and every requested constraint preserved. "
                                f"Correct these errors: {error}"
                            ),
                        )
                    )

        raise LLMResponseError(f"Direction output failed validation: {last_error}")
