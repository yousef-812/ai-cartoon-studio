"use client";

import { FormEvent, useEffect, useState } from "react";

type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type JobStatus = "planned" | "queued" | "running" | "succeeded" | "failed";
type Series = { id: string; name: string };
type DirectionJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  review_status: ReviewStatus;
  result: null | { title: string; scenes: unknown[] };
};
type QcCheck = {
  code: string;
  severity: "info" | "warning" | "error";
  passed: boolean;
  message: string;
  scene_number: number | null;
  shot_number: number | null;
};
type FinalArtifact = {
  kind: string;
  url: string;
  filename: string;
  mime_type: string;
  size_bytes: number | null;
  checksum_sha256: string;
  duration_seconds: number | null;
};
type FinalizationJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    title: string;
    total_duration_seconds: number;
    shots: Array<{ scene_number: number; shot_number: number }>;
    subtitles: Array<{ index: number; text: string; speaker: string }>;
    short_candidates: Array<{ index: number; title: string; duration_seconds: number }>;
    preflight_report: { passed: boolean; checks: QcCheck[] };
  };
  report: null | { passed: boolean; checks: QcCheck[] };
  artifacts: FinalArtifact[];
};
type FinalizationHealth = {
  available: boolean;
  ffmpeg_available: boolean;
  ffprobe_available: boolean;
  detail: string;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function artifactUrl(url: string) {
  return url.startsWith("/") ? `${apiUrl}${url}` : url;
}

function fileSize(bytes: number | null) {
  if (bytes === null) return "";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FinalizationPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [directionId, setDirectionId] = useState("");
  const [jobs, setJobs] = useState<FinalizationJob[]>([]);
  const [health, setHealth] = useState<FinalizationHealth | null>(null);
  const [message, setMessage] = useState(
    "Approve every shot sound mix before final episode assembly.",
  );
  const active = jobs.some((job) => job.status === "queued" || job.status === "running");

  useEffect(() => {
    void loadSeries();
    void loadHealth();
  }, []);

  useEffect(() => {
    if (!seriesId) return;
    void loadProduction(seriesId);
  }, [seriesId]);

  useEffect(() => {
    if (!seriesId || !active) return;
    const timer = window.setInterval(() => void loadJobs(seriesId), 4000);
    return () => window.clearInterval(timer);
  }, [active, seriesId]);

  async function loadSeries() {
    const response = await fetch(`${apiUrl}/api/v1/series`, { cache: "no-store" });
    if (!response.ok) return;
    const data = (await response.json()) as Series[];
    setSeries(data);
    setSeriesId((current) => current || data[0]?.id || "");
  }

  async function loadHealth() {
    const response = await fetch(`${apiUrl}/api/v1/finalization/health`, {
      cache: "no-store",
    });
    if (response.ok) setHealth((await response.json()) as FinalizationHealth);
  }

  async function loadJobs(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/finalization-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setJobs((await response.json()) as FinalizationJob[]);
  }

  async function loadProduction(id: string) {
    const directionResponse = await fetch(`${apiUrl}/api/v1/series/${id}/direction-jobs`, {
      cache: "no-store",
    });
    await loadJobs(id);
    if (!directionResponse.ok) return;
    const data = (await directionResponse.json()) as DirectionJob[];
    const approved = data.filter(
      (job) => job.status === "succeeded" && job.review_status === "approved" && job.result,
    );
    setDirections(approved);
    setDirectionId((current) =>
      approved.some((job) => job.id === current) ? current : approved[0]?.id || "",
    );
  }

  async function action(path: string, success: string, body?: object) {
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail ?? "Finalization action failed.");
      return;
    }
    setMessage(success);
    if (seriesId) await loadJobs(seriesId);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!directionId) return;
    const form = new FormData(event.currentTarget);
    await action(
      `/api/v1/direction-jobs/${directionId}/finalization-jobs/plan`,
      "Final quality control and episode assembly were queued.",
      {
        include_subtitles: form.get("subtitles") === "on",
        burn_subtitles: form.get("burnSubtitles") === "on",
        subtitle_language: String(form.get("language") ?? "en"),
        generate_thumbnail: form.get("thumbnail") === "on",
        shorts_candidate_count: Number(form.get("shortCount") ?? 3),
        shorts_duration_seconds: Number(form.get("shortDuration") ?? 30),
        output_width: Number(form.get("width") ?? 1920),
        output_height: Number(form.get("height") ?? 1080),
        output_fps: Number(form.get("fps") ?? 24),
        video_codec: String(form.get("videoCodec") ?? "libx264"),
        audio_codec: String(form.get("audioCodec") ?? "aac"),
        target_loudness_lufs: Number(form.get("loudness") ?? -16),
        loudness_tolerance_lu: Number(form.get("loudnessTolerance") ?? 2),
        silence_threshold_db: Number(form.get("silenceThreshold") ?? -45),
        max_silence_seconds: Number(form.get("maxSilence") ?? 2),
        max_peak_db: Number(form.get("maxPeak") ?? -1),
      },
    );
  }

  return (
    <main>
      <header>
        <p className="eyebrow">10 · QUALITY CONTROL & FINAL ASSEMBLY</p>
        <h1>Final Episode</h1>
        <p className="lede">
          Validate every approved shot, render the episode master, export subtitles, create a
          thumbnail, and prepare vertical Shorts candidates.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "FINAL RENDER READY" : "FINAL RENDER OFFLINE"}
          </span>
          <small>{health?.detail ?? "Checking FFmpeg and FFprobe..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace full">
        <form onSubmit={createPlan}>
          <p className="eyebrow">DELIVERY PROFILE</p>
          <h2>Render final episode</h2>
          <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)} required>
            <option value="">Select series</option>
            {series.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <select
            value={directionId}
            onChange={(event) => setDirectionId(event.target.value)}
            required
          >
            <option value="">Select approved direction</option>
            {directions.map((job) => (
              <option key={job.id} value={job.id}>
                {job.result?.title ?? job.id} · {job.result?.scenes.length ?? 0} scenes
              </option>
            ))}
          </select>
          <div className="row">
            <label>
              <input name="subtitles" type="checkbox" defaultChecked /> Export subtitles
            </label>
            <label>
              <input name="burnSubtitles" type="checkbox" /> Burn subtitles
            </label>
          </div>
          <label>
            <input name="thumbnail" type="checkbox" defaultChecked /> Generate thumbnail
          </label>
          <div className="row">
            <label>
              Subtitle language
              <input name="language" defaultValue="en" />
            </label>
            <label>
              Shorts candidates
              <input name="shortCount" type="number" min={0} max={6} defaultValue={3} />
            </label>
          </div>
          <label>
            Shorts duration seconds
            <input name="shortDuration" type="number" min={10} max={60} defaultValue={30} />
          </label>
          <div className="row">
            <label>
              Width
              <input name="width" type="number" min={640} max={3840} defaultValue={1920} />
            </label>
            <label>
              Height
              <input name="height" type="number" min={360} max={2160} defaultValue={1080} />
            </label>
          </div>
          <div className="row">
            <label>
              FPS
              <input name="fps" type="number" min={12} max={60} defaultValue={24} />
            </label>
            <label>
              Video codec
              <select name="videoCodec" defaultValue="libx264">
                <option value="libx264">H.264 software</option>
                <option value="libx265">H.265 software</option>
                <option value="h264_nvenc">H.264 NVIDIA</option>
              </select>
            </label>
          </div>
          <label>
            Audio codec
            <select name="audioCodec" defaultValue="aac">
              <option value="aac">AAC</option>
              <option value="libopus">Opus</option>
            </select>
          </label>
          <div className="row">
            <label>
              Target LUFS
              <input name="loudness" type="number" min={-24} max={-5} defaultValue={-16} />
            </label>
            <label>
              LU tolerance
              <input
                name="loudnessTolerance"
                type="number"
                min={0.5}
                max={6}
                step={0.5}
                defaultValue={2}
              />
            </label>
          </div>
          <div className="row">
            <label>
              Silence threshold dB
              <input
                name="silenceThreshold"
                type="number"
                min={-80}
                max={-20}
                defaultValue={-45}
              />
            </label>
            <label>
              Max silence seconds
              <input name="maxSilence" type="number" min={0.2} max={15} defaultValue={2} />
            </label>
          </div>
          <label>
            Max peak dB
            <input name="maxPeak" type="number" min={-12} max={0} step={0.1} defaultValue={-1} />
          </label>
          <button type="submit" disabled={!directionId || !health?.available}>
            Run QC and render final exports
          </button>
          {!health?.available && (
            <p className="warning">FFmpeg and FFprobe must be available before final rendering.</p>
          )}
        </form>

        <aside>
          <p className="eyebrow">FINALIZATION QUEUE</p>
          {jobs.length === 0 && <p className="muted">No final episode jobs yet.</p>}
          {jobs.map((job) => {
            const checks = job.report?.checks ?? job.spec.preflight_report.checks;
            return (
              <article className={`job ${job.status}`} key={job.id}>
                <div className="job-head">
                  <span className="status">{job.status}</span>
                  <small>
                    {job.review_status} · attempt {job.attempts}
                  </small>
                </div>
                <h3>{job.spec.title}</h3>
                <p>
                  {job.spec.shots.length} shots · {job.spec.total_duration_seconds.toFixed(1)}s ·{" "}
                  {job.spec.subtitles.length} subtitles · {job.spec.short_candidates.length} Shorts
                </p>
                {job.error && <p className="error">{job.error}</p>}
                <div className="cue-list">
                  {checks.map((check, index) => (
                    <div className="cue" key={`${check.code}-${index}`}>
                      <strong>
                        {check.passed ? "PASS" : check.severity.toUpperCase()} · {check.code}
                      </strong>
                      <small>{check.message}</small>
                    </div>
                  ))}
                </div>
                {job.artifacts.map((artifact) => (
                  <div className="video-result" key={`${artifact.kind}-${artifact.url}`}>
                    <strong>{artifact.kind.replaceAll("_", " ")}</strong>
                    {artifact.mime_type.startsWith("video/") && (
                      <video controls preload="metadata" src={artifactUrl(artifact.url)} />
                    )}
                    {artifact.mime_type.startsWith("image/") && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img alt={artifact.kind} src={artifactUrl(artifact.url)} />
                    )}
                    <a href={artifactUrl(artifact.url)} target="_blank" rel="noreferrer">
                      Open {artifact.filename}
                    </a>
                    <small>
                      {fileSize(artifact.size_bytes)}
                      {artifact.duration_seconds ? ` · ${artifact.duration_seconds}s` : ""}
                    </small>
                    {artifact.checksum_sha256 && (
                      <code>{artifact.checksum_sha256.slice(0, 20)}…</code>
                    )}
                  </div>
                ))}
                {job.status === "failed" && (
                  <button
                    className="secondary"
                    type="button"
                    onClick={() =>
                      action(
                        `/api/v1/finalization-jobs/${job.id}/retry`,
                        "Finalization queued again.",
                      )
                    }
                  >
                    Retry finalization
                  </button>
                )}
                {job.status === "succeeded" && (
                  <div className="actions">
                    <button
                      type="button"
                      onClick={() =>
                        action(
                          `/api/v1/finalization-jobs/${job.id}/review`,
                          "Final episode approved.",
                          {
                            decision: "approved",
                            notes: "Approved for manual publishing.",
                          },
                        )
                      }
                    >
                      Approve final episode
                    </button>
                    <button
                      className="secondary"
                      type="button"
                      onClick={() =>
                        action(
                          `/api/v1/finalization-jobs/${job.id}/review`,
                          "Final changes requested.",
                          {
                            decision: "changes_requested",
                            notes: "Revise source mixes, subtitles, QC settings, or export profile.",
                          },
                        )
                      }
                    >
                      Request changes
                    </button>
                  </div>
                )}
              </article>
            );
          })}
        </aside>
      </section>
    </main>
  );
}
