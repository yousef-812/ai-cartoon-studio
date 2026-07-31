import pytest

from packages.characters.models import (
    CharacterRead,
    CharacterRole,
    VisualIdentity,
    VoiceProfile,
)
from packages.scripts.models import EpisodeScript
from packages.voices.models import VoicePlanRequest
from packages.voices.planner import VoicePlanner


def test_voice_planner_uses_character_voice_and_dialogue_emotion() -> None:
    script = EpisodeScript(
        title="The Clockwork Cloud",
        language="en",
        target_duration_seconds=180,
        total_estimated_duration_seconds=180,
        cold_open="A frozen cloud pulls the market upward without warning.",
        scenes=[
            {
                "number": 1,
                "title": "Frozen Sky",
                "slugline": "EXT. CLOUD MARKET - DAY",
                "location": "Cloud Market",
                "time_of_day": "day",
                "characters": ["Mira"],
                "objective": "Understand why the market is rising.",
                "conflict": "The frozen cloud keeps pulling buildings upward.",
                "start_state": "Mira is alarmed and searching for an explanation.",
                "end_state": "Mira identifies the damaged cloud engine.",
                "action_lines": ["Mira steadies herself beside a tilted stall."],
                "dialogue": [
                    {
                        "order": 1,
                        "speaker": "Mira",
                        "text": "That cloud is pulling the whole market upward.",
                        "emotion": "focused alarm",
                        "delivery": "fast but clearly articulated",
                        "pause_after_ms": 350,
                        "estimated_duration_seconds": 3.0,
                    }
                ],
                "estimated_duration_seconds": 60,
            },
            {
                "number": 2,
                "title": "Rushed Repair",
                "slugline": "INT. ENGINE ROOM - DAY",
                "location": "Engine Room",
                "time_of_day": "day",
                "characters": ["Mira"],
                "objective": "Restart the cloud engine.",
                "conflict": "The shortcut overloads the mechanism.",
                "start_state": "Mira feels pressured to act immediately.",
                "end_state": "Mira accepts that the repair needs patience.",
                "action_lines": ["The gears stop with a heavy click."],
                "dialogue": [],
                "estimated_duration_seconds": 60,
            },
            {
                "number": 3,
                "title": "Careful Solution",
                "slugline": "INT. ENGINE ROOM - DAY",
                "location": "Engine Room",
                "time_of_day": "day",
                "characters": ["Mira"],
                "objective": "Complete the repair carefully.",
                "conflict": "The city is running out of stable cloud power.",
                "start_state": "Mira follows the full repair sequence.",
                "end_state": "The city returns to balance safely.",
                "action_lines": ["The engine settles into a steady rhythm."],
                "dialogue": [],
                "estimated_duration_seconds": 60,
            },
        ],
        closing_beat="Mira labels the repaired control so the lesson remains visible.",
    )
    character = CharacterRead(
        series_id="series-1",
        name="Mira",
        role=CharacterRole.PROTAGONIST,
        age_range="12-14",
        description="A curious inventor who learns to slow down before acting.",
        personality_traits=["curious", "brave", "impatient"],
        visual_identity=VisualIdentity(
            reference_prompt="Teen inventor with round goggles and an amber jacket."
        ),
        wardrobe={"default": "amber jacket"},
        speaking_style="Quick, optimistic, and precise when solving a problem.",
        voice_profile=VoiceProfile(
            provider="local-openai-compatible-tts",
            voice_id="mira-main",
            language="en",
            description="Young warm voice with bright energy.",
            speed=1.05,
            pitch=1.0,
        ),
    )

    specs = VoicePlanner().plan(
        script,
        [character],
        VoicePlanRequest(response_format="wav", global_speed_multiplier=1.1),
    )

    assert len(specs) == 1
    assert specs[0].character_id == character.id
    assert specs[0].synthesis.voice_id == "mira-main"
    assert specs[0].synthesis.emotion == "focused alarm"
    assert specs[0].synthesis.speed == pytest.approx(1.155)
    assert specs[0].pause_after_ms == 350
