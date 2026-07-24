import asyncio
from typing import Any

from packages.agents.story_agent import StoryAgent
from packages.characters.models import CharacterRead, CharacterRole, VisualIdentity, VoiceProfile
from packages.llm.models import LLMHealth, LLMMessage
from packages.series.models import SeriesRead, SeriesRules, SeriesStatus, VisualStyle
from packages.stories.models import StoryGenerationRequest


class FakeProvider:
    name = "fake-local"
    model = "fake-7b"

    def __init__(self) -> None:
        self.messages: list[LLMMessage] = []

    async def health(self) -> LLMHealth:
        return LLMHealth(available=True, provider=self.name, model=self.model)

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        self.messages = messages
        return {
            "title": "The Clockwork Cloud",
            "logline": "Mira must repair a cloud engine before her floating city loses its balance.",
            "theme": "Patience turns invention into responsibility.",
            "hook": "A golden cloud suddenly freezes above the city and begins pulling streets upward.",
            "synopsis": (
                "Mira rushes to fix the ancient cloud engine, ignores her friend's warning, and "
                "creates a second failure. She learns to slow down, listen, and combine her skill "
                "with the team's knowledge before restoring the city safely."
            ),
            "beats": [
                {"title": "Disruption", "summary": "The cloud engine freezes.", "purpose": "Hook"},
                {
                    "title": "Failure",
                    "summary": "Mira's rushed repair makes it worse.",
                    "purpose": "Escalation",
                },
                {
                    "title": "Repair",
                    "summary": "The team solves it together.",
                    "purpose": "Resolution",
                },
            ],
            "scenes": [
                {
                    "number": 1,
                    "title": "Frozen Sky",
                    "location": "Cloud Market",
                    "characters": ["Mira"],
                    "objective": "Understand why the city is tilting.",
                    "conflict": "The frozen cloud lifts buildings.",
                    "outcome": "Mira finds the damaged engine.",
                    "estimated_duration_seconds": 60,
                },
                {
                    "number": 2,
                    "title": "Rushed Repair",
                    "location": "Cloud Engine Room",
                    "characters": ["Mira"],
                    "objective": "Restart the engine quickly.",
                    "conflict": "Her shortcut overloads the gears.",
                    "outcome": "The problem becomes more dangerous.",
                    "estimated_duration_seconds": 90,
                },
                {
                    "number": 3,
                    "title": "Shared Solution",
                    "location": "Cloud Engine Room",
                    "characters": ["Mira"],
                    "objective": "Repair the engine carefully.",
                    "conflict": "Time is running out.",
                    "outcome": "The city returns to balance.",
                    "estimated_duration_seconds": 90,
                },
            ],
            "ending": "Mira labels the repaired control: listen before launching.",
            "continuity_updates": ["Mira now respects the ancient maintenance manual."],
            "safety_notes": ["No graphic danger; the city evacuation remains calm."],
        }


def test_story_agent_uses_series_and_character_context() -> None:
    provider = FakeProvider()
    agent = StoryAgent(provider)
    series = SeriesRead(
        name="Skykeepers",
        slug="skykeepers",
        logline="Friends protect a floating city powered by imagination.",
        synopsis="A serialized family adventure.",
        genre="adventure comedy",
        target_audience="family 8+",
        primary_language="en",
        status=SeriesStatus.ACTIVE,
        visual_style=VisualStyle(art_direction="Stylized cinematic 2D animation"),
        rules=SeriesRules(world_rules=["Magic always has a visible cost."]),
    )
    character = CharacterRead(
        series_id=series.id,
        name="Mira",
        role=CharacterRole.PROTAGONIST,
        age_range="12-14",
        description="A curious inventor who acts before she finishes planning.",
        personality_traits=["curious", "brave", "impatient"],
        visual_identity=VisualIdentity(
            reference_prompt="Teen inventor with round goggles and an amber jacket."
        ),
        wardrobe={"default": "amber jacket"},
        speaking_style="Fast and optimistic.",
        voice_profile=VoiceProfile(),
    )

    result = asyncio.run(
        agent.run(
            {
                "series": series,
                "characters": [character],
                "locations": [],
                "request": StoryGenerationRequest(
                    premise="A cloud engine freezes during the busiest market day."
                ),
            }
        )
    )

    assert result["title"] == "The Clockwork Cloud"
    assert "Skykeepers" in provider.messages[1].content
    assert "Mira" in provider.messages[1].content
