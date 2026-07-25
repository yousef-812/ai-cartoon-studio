from typing import Any

from pydantic import ValidationError

from packages.agents.base import ProductionAgent
from packages.characters.models import CharacterRead
from packages.llm.errors import LLMResponseError
from packages.llm.models import LLMMessage
from packages.llm.provider import LLMProvider
from packages.series.models import LocationRead, SeriesRead
from packages.stories.models import EpisodeStory, StoryGenerationRequest
from packages.stories.prompts import build_story_messages


class StoryAgent(ProductionAgent):
    name = "story"

    def __init__(self, provider: LLMProvider, validation_retries: int = 1) -> None:
        self.provider = provider
        self.validation_retries = validation_retries

    @staticmethod
    def _validate_story(
        story: EpisodeStory,
        characters: list[CharacterRead],
        locations: list[LocationRead],
        request: StoryGenerationRequest,
    ) -> None:
        registered_characters = {character.name for character in characters}
        unknown_characters = sorted(
            {
                name
                for scene in story.scenes
                for name in scene.characters
                if name not in registered_characters
            }
        )
        if unknown_characters:
            raise ValueError(f"Unknown story characters: {', '.join(unknown_characters)}")

        registered_locations = {location.name for location in locations}
        if registered_locations:
            unknown_locations = sorted(
                {scene.location for scene in story.scenes if scene.location not in registered_locations}
            )
            if unknown_locations:
                raise ValueError(
                    f"Story uses unregistered locations: {', '.join(unknown_locations)}"
                )

        scene_numbers = [scene.number for scene in story.scenes]
        if scene_numbers != list(range(1, len(scene_numbers) + 1)):
            raise ValueError("Story scene numbers must start at 1 and remain sequential")

        duration = sum(scene.estimated_duration_seconds for scene in story.scenes)
        tolerance = max(10, round(request.target_duration_seconds * 0.2))
        if abs(duration - request.target_duration_seconds) > tolerance:
            raise ValueError(
                f"Story scene durations total {duration}s but target is "
                f"{request.target_duration_seconds}s"
            )

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        series = SeriesRead.model_validate(context["series"])
        characters = [CharacterRead.model_validate(item) for item in context.get("characters", [])]
        locations = [LocationRead.model_validate(item) for item in context.get("locations", [])]
        request = StoryGenerationRequest.model_validate(context["request"])
        messages = build_story_messages(series, characters, locations, request)

        last_error: LLMResponseError | ValidationError | ValueError | None = None
        for attempt in range(self.validation_retries + 1):
            try:
                payload = await self.provider.generate_json(
                    messages,
                    temperature=0.35,
                    max_tokens=4096,
                )
                story = EpisodeStory.model_validate(payload)
                self._validate_story(story, characters, locations, request)
                return story.model_dump(mode="json")
            except (LLMResponseError, ValidationError, ValueError) as error:
                last_error = error
                if attempt < self.validation_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "The previous story response was incomplete, invalid, or failed "
                                "validation. Return one complete concise JSON object again and correct "
                                f"these errors: {error}"
                            ),
                        )
                    )

        raise LLMResponseError(f"Story output failed validation: {last_error}")
