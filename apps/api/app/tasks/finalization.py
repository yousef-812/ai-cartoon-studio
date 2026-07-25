import subprocess
import tempfile
from pathlib import Path

from app.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.finalization import SQLFinalizationJobRepository
from packages.finalization.ffmpeg import (
    build_short_command,
    burn_subtitles,
    extract_thumbnail,
    render_episode,
    write_concat_manifest,
)
from packages.finalization.models import QCReport, QCSeverity
from packages.finalization.qc import inspect_media
from packages.finalization.storage import FinalArtifactStore
from packages.finalization.subtitles import render_srt, render_vtt


@celery_app.task(
    bind=True,
    autoretry_for=(OSError, subprocess.SubprocessError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
    name="finalization.render_episode",
)
def render_finalization_job(self, job_id: str) -> None:
    del self
    session = SessionLocal()
    repository = SQLFinalizationJobRepository(session)
    try:
        job = repository.mark_running(job_id)
        if job is None:
            return
        checks = list(job.spec.preflight_report.checks)
        for shot in job.spec.shots:
            shot_checks = inspect_media(
                shot.input_video_path,
                expected_duration=shot.duration_seconds,
                silence_threshold_db=job.spec.request.silence_threshold_db,
                max_silence_seconds=job.spec.request.max_silence_seconds,
                max_peak_db=job.spec.request.max_peak_db,
            )
            for check in shot_checks:
                check.scene_number = shot.scene_number
                check.shot_number = shot.shot_number
            checks.extend(shot_checks)
        report = QCReport(
            passed=all(
                check.passed or check.severity != QCSeverity.ERROR for check in checks
            ),
            checks=checks,
        )
        if not report.passed:
            repository.fail(job_id, "Blocking quality-control checks failed", report)
            return

        store = FinalArtifactStore(settings.storage_path)
        artifacts = []
        with tempfile.TemporaryDirectory(prefix="cartoon-final-") as temporary_directory:
            workdir = Path(temporary_directory)
            manifest = workdir / "shots.txt"
            clean_master = workdir / "episode-master.mp4"
            write_concat_manifest(job.spec, manifest)
            render_episode(job.spec, str(manifest), str(clean_master))

            srt_path = workdir / "episode.srt"
            vtt_path = workdir / "episode.vtt"
            if job.spec.request.include_subtitles:
                srt_path.write_text(render_srt(job.spec.subtitles), encoding="utf-8")
                vtt_path.write_text(render_vtt(job.spec.subtitles), encoding="utf-8")
                artifacts.append(
                    store.persist_file(
                        str(srt_path),
                        series_id=job.series_id,
                        job_id=job.id,
                        filename="episode.srt",
                        kind="subtitle_srt",
                        metadata={"language": job.spec.request.subtitle_language},
                    )
                )
                artifacts.append(
                    store.persist_file(
                        str(vtt_path),
                        series_id=job.series_id,
                        job_id=job.id,
                        filename="episode.vtt",
                        kind="subtitle_vtt",
                        metadata={"language": job.spec.request.subtitle_language},
                    )
                )

            master_path = clean_master
            if job.spec.request.burn_subtitles and job.spec.subtitles:
                subtitled_master = workdir / "episode-subtitled.mp4"
                burn_subtitles(
                    str(clean_master),
                    str(srt_path),
                    str(subtitled_master),
                )
                master_path = subtitled_master
            artifacts.insert(
                0,
                store.persist_file(
                    str(master_path),
                    series_id=job.series_id,
                    job_id=job.id,
                    filename="episode-master.mp4",
                    kind="episode_master",
                    duration_seconds=job.spec.total_duration_seconds,
                    metadata={
                        "title": job.spec.title,
                        "subtitles_burned": job.spec.request.burn_subtitles,
                    },
                ),
            )

            if job.spec.request.generate_thumbnail:
                thumbnail = workdir / "thumbnail.jpg"
                extract_thumbnail(
                    str(master_path),
                    str(thumbnail),
                    max(0.1, job.spec.total_duration_seconds * 0.35),
                )
                artifacts.append(
                    store.persist_file(
                        str(thumbnail),
                        series_id=job.series_id,
                        job_id=job.id,
                        filename="thumbnail.jpg",
                        kind="thumbnail",
                    )
                )

            for candidate in job.spec.short_candidates:
                short_path = workdir / f"short-{candidate.index}.mp4"
                subprocess.run(
                    build_short_command(
                        str(master_path),
                        str(short_path),
                        candidate,
                    ),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                artifacts.append(
                    store.persist_file(
                        str(short_path),
                        series_id=job.series_id,
                        job_id=job.id,
                        filename=f"short-{candidate.index}.mp4",
                        kind="short_candidate",
                        duration_seconds=candidate.duration_seconds,
                        metadata={
                            "scene_number": candidate.scene_number,
                            "title": candidate.title,
                            "start_time_seconds": candidate.start_time_seconds,
                        },
                    )
                )
        repository.complete(job_id, report, artifacts)
    except Exception as exc:
        repository.fail(job_id, str(exc))
        raise
    finally:
        session.close()
