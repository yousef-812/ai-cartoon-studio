from packages.audio.models import SpeechSynthesisSpec
from packages.characters.models import CharacterRead
from packages.scripts.models import EpisodeScript
from packages.voices.models import VoiceLineSpec, VoicePlanRequest


class VoicePlanner:
    def plan(
        self,
        script: EpisodeScript,
        characters: list[CharacterRead],
        request: VoicePlanRequest,
    ) -> list[VoiceLineSpec]:
        character_map = {character.name: character for character in characters}
        specs: list[VoiceLineSpec] = []
        for scene in script.scenes:
            for line in scene.dialogue:
                character = character_map.get(line.speaker)
                if character is None:
                    raise ValueError(f"Dialogue speaker is not registered: {line.speaker}")
                profile = character.voice_profile
                if not profile.voice_id:
                    raise ValueError(
                        f"Character {character.name} does not have a permanent voice_id"
                    )
                speed = min(2.0, max(0.5, profile.speed * request.global_speed_multiplier))
                constraints = ". ".join(request.constraints)
                delivery = (
                    f"{line.delivery}. Character speaking style: {character.speaking_style}. "
                    f"Voice identity: {profile.description}. Additional constraints: {constraints}"
                )
                specs.append(
                    VoiceLineSpec(
                        key=f"scene:{scene.number}:dialogue:{line.order}:voice",
                        scene_number=scene.number,
                        dialogue_order=line.order,
                        character_id=character.id,
                        character_name=character.name,
                        pause_after_ms=line.pause_after_ms,
                        synthesis=SpeechSynthesisSpec(
                            text=line.text,
                            voice_id=profile.voice_id,
                            model=request.model,
                            language=profile.language or script.language,
                            emotion=line.emotion,
                            delivery=delivery,
                            speed=speed,
                            pitch=profile.pitch,
                            response_format=request.response_format,
                            target_duration_seconds=line.estimated_duration_seconds,
                            metadata={
                                "scene_number": scene.number,
                                "dialogue_order": line.order,
                                "character_id": character.id,
                                "character_name": character.name,
                                "pause_after_ms": line.pause_after_ms,
                            },
                        ),
                    )
                )
        if not specs:
            raise ValueError("Approved screenplay does not contain dialogue to synthesize")
        return specs
