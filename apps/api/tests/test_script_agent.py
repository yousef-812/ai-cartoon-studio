import asyncio
from typing import Any

from packages.agents.script_agent import ScriptAgent
from packages.characters.models import CharacterRead, CharacterRole, VisualIdentity, VoiceProfile
from packages.llm.models import LLMHealth, LLMMessage
from packages.scripts.models import ScriptGenerationRequest
from packages.series.models import SeriesRead, SeriesRules, SeriesStatus, VisualStyle
from packages.stories.models import EpisodeStory


class RepairingProvider:
    name = "fake-local"
    model = "fake-7b"

    def __init__(self) -> None:
        self.calls = 0
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
        self.calls += 1
        self.messages = messages
        speaker = "Unknown Hero" if self.calls == 1 else "Mira"
        return {
            "title": "The Clockwork Cloud",
            "language": "en",
            "target_duration_seconds": 180,
            "total_estimated_duration_seconds": 180,
            "cold_open": "A golden cloud freezes above the market and pulls a tower sideways.",
            "scenes": [
                {
                    "number": 1,
                    "title": "Frozen Sky",
                    "slugline": "EXT. CLOUD MARKET - DAY",
                    "location": "Cloud Market",
                    "time_of_day": "day",
                    "characters": ["Mira"],
                    "objective": "Discover why the city is tilting.",
                    "conflict": "The cloud keeps lifting buildings.",
                    "start_state": "Mira is confident and hurried.",
                    "end_state": "Mira locates the damaged engine.",
                    "action_lines": ["Mira catches a rolling toolbox and studies the frozen cloud."],
                    "dialogue": [
                        {
                            "order": 1,
                            "speaker": speaker,
                            "text": "That cloud is not drifting. It is pulling.",
                            "emotion": "focused alarm",
                            "delivery": "fast but controlled",
                            "pause_after_ms": 200,
                            "estimated_duration_seconds": 3.0,
                        }
                    ],
                    "estimated_duration_seconds": 60,
                },
                {
                    "number": 2,
                    "title": "Rushed Repair",
                    "slugline": "INT. CLOUD ENGINE ROOM - DAY",
                    "location": "Cloud Engine Room",
                    "time_of_day": "day",
                    "characters": ["Mira"],
                    "objective": "Restart the engine before the market rises.",
                    "conflict": "Mira's shortcut overloads the gears.",
                    "start_state": "Mira believes speed will solve everything.",
                    "end_state": "Mira accepts that she needs a careful plan.",
                    "action_lines": ["The gears kick backward and Mira shields her face."],
                    "dialogue": [],
                    "estimated_duration_seconds": 60,
                },
                {
                    "number": 3,
                    "title": "Shared Solution",
                    "slugline": "INT. CLOUD ENGINE ROOM - SUNSET",
                    "location": "Cloud Engine Room",
                    "time_of_day": "sunset",
                    "characters": ["Mira"],
                    "objective": "Repair the engine with patience.",
                    "conflict": "The final stabilizer is almost out of time.",
                    "start_state": "Mira slows down and follows the maintenance sequence.",
                    "end_state": "The city returns to balance safely.",
                    "action_lines": ["The engine settles into a warm steady rhythm."],
                    "dialogue": [],
                    "estimated_duration_seconds": 60,
                },
            ],
            "closing_beat": "Mira writes listen first on the repaired control panel.",
            "continuity_updates": ["Mira now respects the maintenance manual."],
            "production_notes": ["Keep danger readable but family friendly."],
        }


def _story() -> EpisodeStory:
    return EpisodeStory(
        title="The Clockwork Cloud",
        logline="Mira must repair a cloud engine before her floating city loses balance.",
        theme="Patience makes invention responsible.",
        hook="A golden cloud freezes above the city and starts lifting buildings.",
        synopsis=(
            "Mira rushes to repair the cloud engine, makes the failure worse, then learns to "
            "slow down and follow a careful sequence before restoring the city safely."
        ),
        beats=[
            {"title": "Disruption", "summary": "The cloud freezes above the market.", "purpose": "Hook"},
            {"title": "Failure", "summary": "A rushed repair overloads the engine.", "purpose": "Escalation"},
            {"title": "Repair", "summary": "Mira repairs it patiently.", "purpose": "Resolution"},
        ],
        scenes=[
            {"number": 1, "title": "Frozen Sky", "location": "Cloud Market", "characters": ["Mira"], "objective": "Find the fault.", "conflict": "Buildings rise.", "outcome": "The engine is located.", "estimated_duration_seconds": 60},
            {"number": 2, "title": "Rushed Repair", "location": "Cloud Engine Room", "characters": ["Mira"], "objective": "Restart it.", "conflict": "The shortcut fails.", "outcome": "Mira changes approach.", "estimated_duration_seconds": 60},
            {"number": 3, "title": "Shared Solution", "location": "Cloud Engine Room", "characters": ["Mira"], "objective": "Repair it carefully.", "conflict": "Time is short.", "outcome": "The city stabilizes.", "estimated_duration_seconds": 60},
        ],
        ending="Mira labels the repaired control so she remembers to listen before launching.",
    )


def test_script_agent_repairs_unknown_speaker_and_preserves_context() -> None:
    provider = RepairingProvider()
    agent = ScriptAgent(provider, validation_retries=1)
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
                "story": _story(),
                "request": ScriptGenerationRequest(target_duration_seconds=180),
            }
        )
    )

    assert provider.calls == 2
    assert result["scenes"][0]["dialogue"][0]["speaker"] == "Mira"
    assert "approved_story" in provider.messages[1].content
