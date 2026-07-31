# Finalization production

The finalization stage converts approved shot mixes into permanent delivery artifacts. It does not bypass upstream approvals and it does not publish automatically.

## Required inputs

A finalization job can be planned only when:

- the direction job succeeded and was approved;
- every directed shot has a successful and approved sound mix;
- every mixed-shot video has been copied into permanent project storage;
- stored source files still exist when the final job is queued or retried.

## Preflight and media QC

The planner verifies shot coverage, timeline continuity, subtitle bounds, and declared shot durations. The render worker then uses FFprobe and FFmpeg to verify each source shot:

- video stream exists;
- audio stream exists;
- actual duration matches the directed duration;
- long silence stays within the configured threshold;
- maximum audio peak stays below the configured ceiling;
- integrated loudness stays within the configured LU tolerance.

Warnings such as excessive silence are visible in the report. Missing streams, duration mismatches, clipping risk, and loudness failures block delivery.

After assembly, the selected final master is inspected again. A job cannot succeed when final-master QC contains a blocking error.

## Rendering

FFmpeg concatenates the ordered shot timeline and normalizes every export to the selected:

- width and height;
- frame rate;
- video codec;
- audio codec;
- stereo 48 kHz audio;
- target integrated loudness and true-peak ceiling.

The default delivery profile is 1920×1080, 24 fps, H.264, AAC, -16 LUFS, and a -1 dB peak ceiling.

## Subtitles

Approved dialogue-placement segments become episode-level subtitle cues. The system can export:

- `episode.srt`;
- `episode.vtt`;
- an optional master with subtitles burned into the picture.

Subtitle timestamps include each shot's position on the final episode timeline.

## Permanent outputs

Successful jobs store files under:

```text
storage/<series-id>/final-episodes/<job-id>/
```

Possible outputs are:

- `episode-master.mp4`;
- `episode.srt`;
- `episode.vtt`;
- `qc-report.json`;
- `thumbnail.jpg`;
- `short-1.mp4` through the configured candidate count.

Every artifact records a stable `/artifacts/...` URL, MIME type, byte size, SHA-256 checksum, duration when relevant, and production metadata.

## API

```text
GET  /api/v1/finalization/health
POST /api/v1/direction-jobs/{direction_job_id}/finalization-jobs/plan
GET  /api/v1/series/{series_id}/finalization-jobs
GET  /api/v1/finalization-jobs/{job_id}
POST /api/v1/finalization-jobs/{job_id}/retry
POST /api/v1/finalization-jobs/{job_id}/review
```

Dashboard: `/finalization`

Final approval marks the delivery package ready for manual publishing. Publishing credentials and automatic platform uploads are intentionally outside this stage.
