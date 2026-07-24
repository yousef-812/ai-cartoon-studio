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
        unknown_characters = sorted(
            {
                name
                for scene in direction.scenes
                for shot in scene.shots
                for name in shot.characters
                if name not in registered
            }
        )
        if unknown_characters:
            raise ValueError(f"Unknown shot characters: {', '.join(unknown_characters)}")

        if len(direction.scenes) != len(script.scenes):
            raise ValueError("The direction plan must preserve every screenplay scene")

        for directed_scene, script_scene in zip(direction.scenes, script.scenes, strict=True):
            if directed_scene.scene_number != script_scene.number:
                raise ValueError("Directed scene numbers must match screenplay scene numbers")

            valid_lines = {line.order for line in script_scene.dialogue}
            covered_lines = {
                order for shot in directed_scene.shots for order in shot.dialogue_line_orders
            }
            if covered_lines != valid_lines:
                raise ValueError(
                    f"Scene {script_scene.number} shots must cover every dialogue line exactly by order"
                )
            if any(
                shot.duration_seconds > request.max_shot_duration_seconds
                for shot in directed_scene.shots
            ):
                raise ValueError(
                    f"A shot exceeds the {request.max_shot_duration_seconds}s maximum duration"
                )

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        series = SeriesRead.model_validate(context["series"])
        characters = [CharacterRead.model_validate(item) for item in context.get("characters", [])]
        locations = [LocationRead.model_validate(item) for item in context.get("locations", [])]
        script = EpisodeScript.model_validate(context["script"])
        request = DirectionGenerationRequest.model_validate(context["request"])
        messages = build_direction_messages(series, characters, locations, script, request)

        last_error: ValidationError | ValueError | None = None
        for attempt in range(self.validation_retries + 1):
            payload = await self.provider.generate_json(messages)
            try:
                direction = EpisodeDirection.model_validate(payload)
                self._validate_plan(direction, script, characters, request)
                return direction.model_dump(mode="json")
            except (ValidationError, ValueError) as error:
                last_error = error
                if attempt < self.validation_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "The previous direction JSON failed validation. Return the complete "
                                f"JSON again after correcting these errors: {error}"
                            ),
                        )
                    )

        raise LLMResponseError(f"Direction output failed validation: {last_error}")
