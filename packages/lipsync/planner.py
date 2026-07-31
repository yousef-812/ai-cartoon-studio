from pathlib import Path

from packages.animations.models import (
    AnimationJobRead,
    AnimationJobStatus,
    AnimationReviewStatus,
)
from packages.direction.models import EpisodeDirection
from packages.lipsync.models import (
    DialoguePlacementSegment,
    LipSyncGenerationSpec,
    LipSyncPlanRequest,
    LipSyncShotSpec,
)
from packages.voices.models import VoiceJobRead, VoiceJobStatus, VoiceReviewStatus


class LipSyncPlanner:
    def plan(
        self,
        direction: EpisodeDirection,
        animations: list[AnimationJobRead],
        voices: list[VoiceJobRead],
        request: LipSyncPlanRequest,
    ) -> list[LipSyncShotSpec]:
        animation_map = {
            (job.spec.scene_number, job.spec.shot_number): job
            for job in animations
        }
        voice_map = {
            (job.spec.scene_number, job.spec.dialogue_order): job
            for job in voices
        }
        specs: list[LipSyncShotSpec] = []

        for scene in direction.scenes:
            for shot in scene.shots:
                if not shot.dialogue_line_orders:
                    continue
                animation = animation_map.get((scene.scene_number, shot.number))
                if animation is None:
                    raise ValueError(
                        f"Animated shot is missing for scene {scene.scene_number} shot {shot.number}"
                    )
                self._validate_animation(animation)
                duration = animation.spec.generation.duration_seconds
                cursor = request.lead_in_ms / 1000
                segments: list[DialoguePlacementSegment] = []

                for dialogue_order in shot.dialogue_line_orders:
                    voice = voice_map.get((scene.scene_number, dialogue_order))
                    if voice is None:
                        raise ValueError(
                            f"Voice line {dialogue_order} is missing in scene {scene.scene_number}"
                        )
                    self._validate_voice(voice)
                    assert voice.audio is not None
                    line_duration = (
                        voice.audio.duration_seconds
                        or voice.spec.synthesis.target_duration_seconds
                    )
                    if line_duration is None or line_duration <= 0:
                        raise ValueError(
                            f"Voice line {dialogue_order} does not have usable duration metadata"
                        )
                    start = round(cursor, 3)
                    end = round(start + line_duration, 3)
                    available_end = duration - (request.tail_padding_ms / 1000)
                    if end > available_end:
                        raise ValueError(
                            f"Dialogue exceeds scene {scene.scene_number} shot {shot.number}; "
                            "split the shot, reduce dialogue, or regenerate voice timing"
                        )
                    segments.append(
                        DialoguePlacementSegment(
                            voice_job_id=voice.id,
                            dialogue_order=dialogue_order,
                            character_id=voice.character_id,
                            character_name=voice.spec.character_name,
                            audio_path=voice.audio.storage_path,
                            start_time_seconds=start,
                            end_time_seconds=end,
                            pause_after_ms=voice.spec.pause_after_ms,
                            face_hint=(
                                f"Track and animate only {voice.spec.character_name}'s visible face. "
                                f"Characters in shot: {', '.join(shot.characters)}."
                            ),
                            text=voice.spec.synthesis.text,
                        )
                    )
                    gap = max(request.minimum_gap_ms, voice.spec.pause_after_ms) / 1000
                    cursor = end + gap

                specs.append(
                    LipSyncShotSpec(
                        key=f"scene:{scene.scene_number}:shot:{shot.number}:lip-sync",
                        animation_job_id=animation.id,
                        generation=LipSyncGenerationSpec(
                            input_video_path=animation.videos[0].storage_path,
                            scene_number=scene.scene_number,
                            shot_number=shot.number,
                            duration_seconds=duration,
                            segments=segments,
                            model=request.model,
                            quality=request.quality,
                            face_detection_confidence=request.face_detection_confidence,
                            preserve_original_audio=request.preserve_original_audio,
                            constraints=request.constraints,
                            metadata={
                                "direction_job_id": animation.direction_job_id,
                                "animation_job_id": animation.id,
                                "characters": shot.characters,
                                "dialogue_line_orders": shot.dialogue_line_orders,
                            },
                        ),
                    )
                )

        if not specs:
            raise ValueError("Approved direction does not contain dialogue shots to lip-sync")
        return specs

    @staticmethod
    def _validate_animation(job: AnimationJobRead) -> None:
        if job.status != AnimationJobStatus.SUCCEEDED:
            raise ValueError("Animated shot must finish successfully before lip sync")
        if job.review_status != AnimationReviewStatus.APPROVED:
            raise ValueError("Approve the animated shot before lip sync")
        if not job.videos or not job.videos[0].storage_path:
            raise ValueError("Animated shot is not stored permanently")
        if not Path(job.videos[0].storage_path).is_file():
            raise ValueError("Stored animated shot file is missing")

    @staticmethod
    def _validate_voice(job: VoiceJobRead) -> None:
        if job.status != VoiceJobStatus.SUCCEEDED:
            raise ValueError("Voice line must finish successfully before lip sync")
        if job.review_status != VoiceReviewStatus.APPROVED:
            raise ValueError("Approve every voice line before lip sync")
        if job.audio is None or not job.audio.storage_path:
            raise ValueError("Voice line is not stored permanently")
        if not Path(job.audio.storage_path).is_file():
            raise ValueError("Stored voice line file is missing")
