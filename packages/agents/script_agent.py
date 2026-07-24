from typing import Any

from pydantic import ValidationError

from packages.agents.base import ProductionAgent
from packages.characters.models import CharacterRead
from packages.llm.errors import LLMResponseError
from packages.llm.models import LLMMessage
from packages.llm.provider import LLMProvider
from packages.scripts.models import EpisodeScript, ScriptGenerationRequest
from packages.scripts.prompts import build_script_messages
from packages.series.models import LocationRead, SeriesRead
from packages.stories.models import EpisodeStory


class ScriptAgent(ProductionAgent):
    name = "script"

    def __init__(self, provider: LLMProvider, validation_retries: int = 1) -> None:
        self.provider = provider
        self.validation_retries = validation_retries

    @staticmethod
    def _validate_identity(script: EpisodeScript, characters: list[CharacterRead]) -> None:
        registered = {character.name for character in characters}
        unknown_speakers = sorted(
            {
                line.speaker
                for scene in script.scenes
                for line in scene.dialogue
                if line.speaker not in registered
            }
        )
        unknown_scene_characters = sorted(
            {
                name
                for scene in script.scenes
                for name in scene.characters
                if name not in registered
            }
        )
        if unknown_speakers:
            raise ValueError(f"Unknown dialogue speakers: {', '.join(unknown_speakers)}")
        if unknown_scene_characters:
            raise ValueError(
                f"Unknown scene characters: {', '.join(unknown_scene_characters)}"
            )

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        series = SeriesRead.model_validate(context["series"])
        characters = [CharacterRead.model_validate(item) for item in context.get("characters", [])]
        locations = [LocationRead.model_validate(item) for item in context.get("locations", [])]
        story = EpisodeStory.model_validate(context["story"])
        request = ScriptGenerationRequest.model_validate(context["request"])
        messages = build_script_messages(series, characters, locations, story, request)

        last_error: ValidationError | ValueError | None = None
        for attempt in range(self.validation_retries + 1):
            payload = await self.provider.generate_json(messages)
            try:
                script = EpisodeScript.model_validate(payload)
                self._validate_identity(script, characters)
                return script.model_dump(mode="json")
            except (ValidationError, ValueError) as error:
                last_error = error
                if attempt < self.validation_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "The previous screenplay JSON failed validation. Return the complete "
                                f"JSON again after correcting these errors: {error}"
                            ),
                        )
                    )

        raise LLMResponseError(f"Script output failed validation: {last_error}")
