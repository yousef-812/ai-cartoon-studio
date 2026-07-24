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

    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        series = SeriesRead.model_validate(context["series"])
        characters = [CharacterRead.model_validate(item) for item in context.get("characters", [])]
        locations = [LocationRead.model_validate(item) for item in context.get("locations", [])]
        request = StoryGenerationRequest.model_validate(context["request"])
        messages = build_story_messages(series, characters, locations, request)

        last_error: ValidationError | None = None
        for attempt in range(self.validation_retries + 1):
            payload = await self.provider.generate_json(messages)
            try:
                story = EpisodeStory.model_validate(payload)
                return story.model_dump(mode="json")
            except ValidationError as error:
                last_error = error
                if attempt < self.validation_retries:
                    messages.append(
                        LLMMessage(
                            role="user",
                            content=(
                                "The previous JSON failed schema validation. Return the complete JSON "
                                f"again after correcting these errors: {error}"
                            ),
                        )
                    )

        raise LLMResponseError(f"Story output failed validation: {last_error}")
