from pathlib import Path

from packages.direction.models import EpisodeDirection
from packages.finalization.models import (
    FinalizationJobSpec,
    FinalizationPlanRequest,
    FinalShotSpec,
    QCCheck,
    QCReport,
    QCSeverity,
    ShortCandidateSpec,
    SubtitleCue,
)
from packages.lipsync.models import LipSyncJobRead
from packages.sound.models import (
    SoundMixJobRead,
    SoundMixJobStatus,
    SoundMixReviewStatus,
)


class FinalizationPlanner:
    def plan(
        self,
        direction_job_id: str,
        direction: EpisodeDirection,
        sound_jobs: list[SoundMixJobRead],
        lip_sync_jobs: list[LipSyncJobRead],
        request: FinalizationPlanRequest,
    ) -> FinalizationJobSpec:
        sound_map = {
            (job.spec.generation.scene_number, job.spec.generation.shot_number): job
            for job in sound_jobs
        }
        lip_sync_map = {job.id: job for job in lip_sync_jobs}
        checks: list[QCCheck] = []
        shots: list[FinalShotSpec] = []
        subtitles: list[SubtitleCue] = []
        scene_ranges: list[tuple[int, str, float, float, int]] = []
        cursor = 0.0
        subtitle_index = 1

        for scene in direction.scenes:
            scene_start = cursor
            dialogue_count = 0
            for shot in scene.shots:
                key = (scene.scene_number, shot.number)
                job = sound_map.get(key)
                if job is None:
                    raise ValueError(
                        f"Approved sound mix is missing for scene {scene.scene_number} shot {shot.number}"
                    )
                self._validate_sound_job(job)
                video = job.videos[0]
                duration = shot.duration_seconds
                if video.duration_seconds is not None:
                    delta = abs(video.duration_seconds - duration)
                    checks.append(
                        QCCheck(
                            code="shot_duration",
                            severity=QCSeverity.ERROR if delta > 0.25 else QCSeverity.INFO,
                            passed=delta <= 0.25,
                            message=(
                                f"Scene {scene.scene_number} shot {shot.number} duration delta "
                                f"is {delta:.3f}s"
                            ),
                            scene_number=scene.scene_number,
                            shot_number=shot.number,
                            metadata={"expected": duration, "actual": video.duration_seconds},
                        )
                    )
                    if delta > 0.25:
                        raise ValueError("Approved sound mix duration does not match directed shot")
                shots.append(
                    FinalShotSpec(
                        sound_job_id=job.id,
                        scene_number=scene.scene_number,
                        shot_number=shot.number,
                        input_video_path=video.storage_path,
                        duration_seconds=duration,
                        timeline_start_seconds=round(cursor, 3),
                        timeline_end_seconds=round(cursor + duration, 3),
                        transition=shot.transition,
                    )
                )
                if request.include_subtitles and job.source_job_type == "lip_sync":
                    source = lip_sync_map.get(job.source_job_id)
                    if source is None:
                        raise ValueError("Lip-sync source is missing for subtitle generation")
                    for segment in source.spec.generation.segments:
                        text = segment.text.strip()
                        if not text:
                            continue
                        subtitles.append(
                            SubtitleCue(
                                index=subtitle_index,
                                start_time_seconds=round(cursor + segment.start_time_seconds, 3),
                                end_time_seconds=round(cursor + segment.end_time_seconds, 3),
                                text=text,
                                speaker=segment.character_name,
                            )
                        )
                        subtitle_index += 1
                        dialogue_count += 1
                cursor += duration
            scene_ranges.append(
                (scene.scene_number, scene.title, scene_start, cursor, dialogue_count)
            )

        checks.append(
            QCCheck(
                code="shot_coverage",
                severity=QCSeverity.INFO,
                passed=len(shots) == sum(len(scene.shots) for scene in direction.scenes),
                message=f"All {len(shots)} directed shots have approved sound mixes",
            )
        )
        checks.append(
            QCCheck(
                code="subtitle_bounds",
                severity=QCSeverity.ERROR,
                passed=all(cue.end_time_seconds <= cursor + 0.05 for cue in subtitles),
                message=f"{len(subtitles)} subtitle cues fit inside the episode timeline",
            )
        )
        report = QCReport(passed=all(check.passed or check.severity != QCSeverity.ERROR for check in checks), checks=checks)
        candidates = self._short_candidates(scene_ranges, request)
        return FinalizationJobSpec(
            title=direction.title,
            direction_job_id=direction_job_id,
            shots=shots,
            subtitles=subtitles,
            short_candidates=candidates,
            total_duration_seconds=round(cursor, 3),
            request=request,
            preflight_report=report,
        )

    @staticmethod
    def _validate_sound_job(job: SoundMixJobRead) -> None:
        if job.status != SoundMixJobStatus.SUCCEEDED:
            raise ValueError("Every sound mix must finish successfully before finalization")
        if job.review_status != SoundMixReviewStatus.APPROVED:
            raise ValueError("Every sound mix must be approved before finalization")
        if not job.videos or not job.videos[0].storage_path:
            raise ValueError("Approved sound mix is not stored permanently")
        if not Path(job.videos[0].storage_path).is_file():
            raise ValueError("Stored sound mix file is missing")

    @staticmethod
    def _short_candidates(
        scene_ranges: list[tuple[int, str, float, float, int]],
        request: FinalizationPlanRequest,
    ) -> list[ShortCandidateSpec]:
        if request.shorts_candidate_count == 0:
            return []
        ranked = sorted(
            scene_ranges,
            key=lambda item: (item[4], item[3] - item[2]),
            reverse=True,
        )[: request.shorts_candidate_count]
        candidates: list[ShortCandidateSpec] = []
        for index, (scene_number, title, start, end, _) in enumerate(ranked, start=1):
            scene_duration = end - start
            duration = min(request.shorts_duration_seconds, scene_duration)
            candidates.append(
                ShortCandidateSpec(
                    index=index,
                    start_time_seconds=round(start, 3),
                    duration_seconds=round(max(5.0, duration), 3),
                    title=title,
                    scene_number=scene_number,
                )
            )
        return candidates
