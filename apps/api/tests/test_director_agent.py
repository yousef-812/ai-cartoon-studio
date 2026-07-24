import asyncio
from typing import Any

from packages.agents.director_agent import DirectorAgent
from packages.characters.models import CharacterRead, CharacterRole, VisualIdentity, VoiceProfile
from packages.direction.models import DirectionGenerationRequest
from packages.llm.models import LLMHealth, LLMMessage
from packages.scripts.models import EpisodeScript
from packages.series.models import SeriesRead, SeriesRules, SeriesStatus, VisualStyle


class RepairingDirectorProvider:
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
        first_character = "Unknown Hero" if self.calls == 1 else "Mira"
        scenes: list[dict[str, Any]] = []
        for scene_number, title, location in [
            (1, "Frozen Sky", "Cloud Market"),
            (2, "Rushed Repair", "Cloud Engine Room"),
            (3, "Careful Solution", "Cloud Engine Room"),
        ]:
            shots = []
            for shot_number in (1, 2):
                dialogue_orders = [1] if scene_number == 1 and shot_number == 2 else []
                shots.append(
                    {
                        "number": shot_number,
                        "scene_number": scene_number,
                        "duration_seconds": 30.0,
                        "shot_size": "wide" if shot_number == 1 else "medium close-up",
                        "camera_angle": "eye level",
                        "camera_movement": "slow push" if shot_number == 2 else "locked",
                        "composition": "Clear foreground action with readable silhouette and depth.",
                        "location": location,
                        "characters": [first_character],
                        "action": "Mira studies the problem and takes a deliberate action.",
                        "emotion": "focused concern",
                        "dialogue_line_orders": dialogue_orders,
                        "visual_prompt": "Stylized cinematic 2D animation, warm light, clear silhouette.",
                        "animation_notes": ["Keep body mechanics readable."],
                        "continuity_requirements": ["Mira keeps her amber jacket and goggles."],
                        "transition": "cut",
                    }
                )
            scenes.append(
                {
                    "scene_number": scene_number,
                    "title": title,
                    "estimated_duration_seconds": 60.0,
                    "shots": shots,
                }
            )
        return {
            "title": "The Clockwork Cloud",
            "aspect_ratio": "16:9",
            "total_estimated_duration_seconds": 180.0,
            "scenes": scenes,
            "global_visual_notes": ["Preserve the warm amber and navy palette."],
            "continuity_notes": ["The city remains above the permanent cloud layer."],
            "production_risks": ["Cloud motion must stay consistent across cuts."],
        }


def _script() -> EpisodeScript:
    scenes = []
    for number, title, location in [
        (1, "Frozen Sky", "Cloud Market"),
        (2, "Rushed Repair", "Cloud Engine Room"),
        (3, "Careful Solution", "Cloud Engine Room"),
    ]:
        dialogue = []
        if number == 1:
            dialogue = [
                {
                    "order": 1,
                    "speaker": "Mira",
                    "text": "That cloud is pulling the market upward.",
                    "emotion": "focused alarm",
                    "estimated_duration_seconds": 3.0,
                }
            ]
        scenes.append(
            {
                "number": number,
                "title": title,
                "slugline": f"INT. {location.upper()} - DAY",
                "location": location,
                "time_of_day": "day",
                "characters": ["Mira"],
                "objective": "Solve the immediate production problem.",
                "conflict": "The failure escalates while time runs short.",
                "start_state": "Mira begins uncertain but determined.",
                "end_state": "Mira gains clarity and advances the solution.",
                "action_lines": ["Mira studies the mechanism."],
                "dialogue": dialogue,
                "estimated_duration_seconds": 60,
            }
        )
    return EpisodeScript(
        title="The Clockwork Cloud",
        language="en",
        target_duration_seconds=180,
        total_estimated_duration_seconds=180,
        cold_open="A frozen cloud pulls the market upward without warning.",
        scenes=scenes,
        closing_beat="Mira labels the repaired control and smiles at the steady cloud.",
    )


def test_director_agent_repairs_unknown_character_and_covers_dialogue() -> None:
    provider = RepairingDirectorProvider()
    agent = DirectorAgent(provider, validation_retries=1)
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
        description="A curious inventor who learns to slow down.",
        personality_traits=["curious", "brave", "impatient"],
        visual_identity=VisualIdentity(
            reference_prompt="Teen inventor with round goggles and an amber jacket."
        ),
        wardrobe={"default": "amber jacket, navy trousers, cream boots"},
        speaking_style="Fast, optimistic, and precise when focused.",
        voice_profile=VoiceProfile(),
    )

    result = asyncio.run(
        agent.run(
            {
                "series": series,
                "characters": [character],
                "locations": [],
                "script": _script(),
                "request": DirectionGenerationRequest(max_shot_duration_seconds=30),
            }
        )
    )

    assert provider.calls == 2
    assert result["scenes"][0]["shots"][0]["characters"] == ["Mira"]
    assert result["scenes"][0]["shots"][1]["dialogue_line_orders"] == [1]
    assert "approved_screenplay" in provider.messages[1].content
