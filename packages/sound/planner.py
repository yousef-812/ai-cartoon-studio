from pathlib import Path

from packages.animations.models import (
    AnimationJobRead,
    AnimationJobStatus,
    AnimationReviewStatus,
)
from packages.direction.models import EpisodeDirection, ShotPlan
from packages.lipsync.models import (
    LipSyncJobRead,
    LipSyncJobStatus,
    LipSyncReviewStatus,
)
from packages.sound.models import (
    DialogueDuckingWindow,
    SoundCueKind,
    SoundCueSpec,
    SoundMixGenerationSpec,
    SoundMixJobSpec,
    SoundPlanRequest,
)


class SoundDesignPlanner:
    def plan(
        self,
        direction: EpisodeDirection,
        animations: list[AnimationJobRead],
        lip_sync_jobs: list[LipSyncJobRead],
        request: SoundPlanRequest,
    ) -> list[SoundMixJobSpec]:
        animation_map = {
            (job.spec.scene_number, job.spec.shot_number): job for job in animations
        }
        lip_sync_map = {
            (job.spec.generation.scene_number, job.spec.generation.shot_number): job
            for job in lip_sync_jobs
        }
        specs: list[SoundMixJobSpec] = []
        for scene in direction.scenes:
            for shot in scene.shots:
                has_dialogue = bool(shot.dialogue_line_orders)
                if has_dialogue:
                    source = lip_sync_map.get((scene.scene_number, shot.number))
                    if source is None:
                        raise ValueError(
                            f"Approved lip-sync shot is missing for scene {scene.scene_number} "
                            f"shot {shot.number}"
                        )
                    self._validate_lip_sync(source)
                    source_type = "lip_sync"
                    source_path = source.videos[0].storage_path
                    source_job_id = source.id
                    dialogue_windows = [
                        DialogueDuckingWindow(
                            start_time_seconds=segment.start_time_seconds,
                            end_time_seconds=segment.end_time_seconds,
                        )
                        for segment in source.spec.generation.segments
                    ]
                else:
                    source = animation_map.get((scene.scene_number, shot.number))
                    if source is None:
                        raise ValueError(
                            f"Approved animated shot is missing for scene {scene.scene_number} "
                            f"shot {shot.number}"
                        )
                    self._validate_animation(source)
                    source_type = "animation"
                    source_path = source.videos[0].storage_path
                    source_job_id = source.id
                    dialogue_windows = []

                cues = self._build_cues(shot, scene.title, request)
                specs.append(
                    SoundMixJobSpec(
                        key=f"scene:{scene.scene_number}:shot:{shot.number}:sound-mix",
                        source_job_type=source_type,
                        source_job_id=source_job_id,
                        generation=SoundMixGenerationSpec(
                            input_video_path=source_path,
                            source_has_dialogue=has_dialogue,
                            scene_number=scene.scene_number,
                            shot_number=shot.number,
                            duration_seconds=shot.duration_seconds,
                            cues=cues,
                            dialogue_windows=dialogue_windows,
                            dialogue_ducking_db=request.dialogue_ducking_db,
                            target_loudness_lufs=request.target_loudness_lufs,
                            constraints=request.constraints,
                            metadata={
                                "direction_title": direction.title,
                                "scene_title": scene.title,
                                "location": shot.location,
                                "characters": shot.characters,
                                "transition": shot.transition,
                            },
                        ),
                    )
                )
        if not specs:
            raise ValueError("Approved direction does not contain shots for sound design")
        return specs

    @staticmethod
    def _build_cues(
        shot: ShotPlan,
        scene_title: str,
        request: SoundPlanRequest,
    ) -> list[SoundCueSpec]:
        cues: list[SoundCueSpec] = []
        scene_key = f"scene:{shot.scene_number}:shot:{shot.number}"
        if request.include_ambience:
            cues.append(
                SoundCueSpec(
                    key=f"{scene_key}:ambience",
                    kind=SoundCueKind.AMBIENCE,
                    prompt=(
                        f"Seamless environmental ambience for {shot.location}. "
                        f"Scene: {scene_title}. Visible action: {shot.action}. "
                        f"Emotional atmosphere: {shot.emotion}. No speech, no melody."
                    ),
                    duration_seconds=shot.duration_seconds,
                    gain_db=request.ambience_gain_db,
                    loop=True,
                    fade_in_seconds=min(0.25, shot.duration_seconds / 4),
                    fade_out_seconds=min(0.35, shot.duration_seconds / 4),
                    model=request.sound_model,
                    metadata={"location": shot.location, "shot_action": shot.action},
                )
            )
        if request.include_effects:
            effect_duration = min(3.0, max(0.4, shot.duration_seconds * 0.4))
            effect_start = min(
                max(0.0, shot.duration_seconds * 0.12),
                max(0.0, shot.duration_seconds - effect_duration),
            )
            cues.append(
                SoundCueSpec(
                    key=f"{scene_key}:effect:1",
                    kind=SoundCueKind.EFFECT,
                    prompt=(
                        f"Production sound effect matching this visible action: {shot.action}. "
                        f"Location: {shot.location}. Camera framing: {shot.shot_size}. "
                        "One clean effect layer, no voice and no music."
                    ),
                    start_time_seconds=round(effect_start, 3),
                    duration_seconds=round(effect_duration, 3),
                    gain_db=request.effects_gain_db,
                    fade_in_seconds=0.02,
                    fade_out_seconds=min(0.15, effect_duration / 3),
                    model=request.sound_model,
                    metadata={"action": shot.action},
                )
            )
        if request.include_music:
            cues.append(
                SoundCueSpec(
                    key=f"{scene_key}:music",
                    kind=SoundCueKind.MUSIC,
                    prompt=(
                        f"Instrumental cinematic underscore for scene '{scene_title}'. "
                        f"Emotion: {shot.emotion}. Action: {shot.action}. "
                        "Animation-friendly, dialogue-safe, no vocals, no recognizable melody, "
                        "clean loopable ending."
                    ),
                    duration_seconds=shot.duration_seconds,
                    gain_db=request.music_gain_db,
                    loop=True,
                    fade_in_seconds=min(0.5, shot.duration_seconds / 4),
                    fade_out_seconds=min(0.7, shot.duration_seconds / 4),
                    model=request.music_model or request.sound_model,
                    metadata={"emotion": shot.emotion, "scene_title": scene_title},
                )
            )
        if not cues:
            raise ValueError("Enable at least one sound layer")
        return cues

    @staticmethod
    def _validate_animation(job: AnimationJobRead) -> None:
        if job.status != AnimationJobStatus.SUCCEEDED:
            raise ValueError("Animated shot must finish successfully before sound design")
        if job.review_status != AnimationReviewStatus.APPROVED:
            raise ValueError("Approve every silent animated shot before sound design")
        if not job.videos or not job.videos[0].storage_path:
            raise ValueError("Animated shot is not stored permanently")
        if not Path(job.videos[0].storage_path).is_file():
            raise ValueError("Stored animated shot file is missing")

    @staticmethod
    def _validate_lip_sync(job: LipSyncJobRead) -> None:
        if job.status != LipSyncJobStatus.SUCCEEDED:
            raise ValueError("Lip-sync shot must finish successfully before sound design")
        if job.review_status != LipSyncReviewStatus.APPROVED:
            raise ValueError("Approve every speaking lip-sync shot before sound design")
        if not job.videos or not job.videos[0].storage_path:
            raise ValueError("Lip-sync shot is not stored permanently")
        if not Path(job.videos[0].storage_path).is_file():
            raise ValueError("Stored lip-sync shot file is missing")
