"use client";

import { FormEvent, useEffect, useState } from "react";

type JobStatus = "planned" | "queued" | "running" | "succeeded" | "failed";
type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type Series = { id: string; name: string };
type DirectionJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  review_status: ReviewStatus;
  result: null | { title: string; scenes: unknown[] };
};
type Segment = {
  dialogue_order: number;
  character_name: string;
  start_time_seconds: number;
  end_time_seconds: number;
  text: string;
};
type LipSyncJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    generation: {
      scene_number: number;
      shot_number: number;
      duration_seconds: number;
      quality: string;
      segments: Segment[];
    };
  };
  videos: Array<{
    url: string;
    filename: string;
    size_bytes: number | null;
    checksum_sha256: string;
  }>;
};
type ProviderHealth = { available: boolean; provider: string; detail: string };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function artifactUrl(url: string) {
  return url.startsWith("/") ? `${apiUrl}${url}` : url;
}

export default function LipSyncPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [directionId, setDirectionId] = useState("");
  const [jobs, setJobs] = useState<LipSyncJob[]>([]);
  const [health, setHealth] = useState<ProviderHealth | null>(null);
  const [message, setMessage] = useState(
    "Approve animated clips and every voice line before planning lip sync.",
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
    const response = await fetch(`${apiUrl}/api/v1/lip-sync/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as ProviderHealth);
  }

  async function loadJobs(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/lip-sync-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setJobs((await response.json()) as LipSyncJob[]);
  }

  async function loadProduction(id: string) {
    const [directionResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/direction-jobs`, { cache: "no-store" }),
      loadJobs(id),
    ]);
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
    if (!response.ok) return setMessage(data.detail ?? "Lip-sync action failed.");
    setMessage(success);
    if (seriesId) await loadJobs(seriesId);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!directionId) return;
    const form = new FormData(event.currentTarget);
    await action(
      `/api/v1/direction-jobs/${directionId}/lip-sync-jobs/plan`,
      "Dialogue placement was validated and lip-sync shots were queued.",
      {
        lead_in_ms: Number(form.get("leadIn") ?? 250),
        tail_padding_ms: Number(form.get("tailPadding") ?? 250),
        minimum_gap_ms: Number(form.get("minimumGap") ?? 120),
        model: String(form.get("model") ?? ""),
        quality: String(form.get("quality") ?? "production"),
        face_detection_confidence: Number(form.get("confidence") ?? 0.7),
        preserve_original_audio: form.get("preserveAudio") === "on",
        constraints: String(form.get("constraints") ?? "").split("\n").filter(Boolean),
      },
    );
  }

  return (
    <main>
      <header>
        <p className="eyebrow">08 · LIP SYNC & DIALOGUE PLACEMENT</p>
        <h1>Lip Sync</h1>
        <p className="lede">
          Place every approved voice line on the directed shot timeline, track the correct speaking
          character, and produce one permanent lip-synced video per dialogue shot.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "LIP SYNC ONLINE" : "LIP SYNC OFFLINE"}
          </span>
          <small>{health?.detail ?? "Checking self-hosted lip-sync worker..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>Check again</button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <form onSubmit={createPlan}>
          <p className="eyebrow">DIALOGUE TIMELINE</p>
          <h2>Plan speaking shots</h2>
          <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)} required>
            <option value="">Select series</option>
            {series.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <select value={directionId} onChange={(event) => setDirectionId(event.target.value)} required>
            <option value="">Select approved direction</option>
            {directions.map((job) => (
              <option key={job.id} value={job.id}>
                {job.result?.title ?? job.id} · {job.result?.scenes.length ?? 0} scenes
              </option>
            ))}
          </select>
          <div className="row">
            <label>Lead-in milliseconds<input name="leadIn" type="number" min={0} max={5000} defaultValue={250} /></label>
            <label>Tail padding milliseconds<input name="tailPadding" type="number" min={0} max={5000} defaultValue={250} /></label>
          </div>
          <div className="row">
            <label>Minimum line gap<input name="minimumGap" type="number" min={0} max={5000} defaultValue={120} /></label>
            <label>Face confidence<input name="confidence" type="number" min={0} max={1} step="0.05" defaultValue={0.7} /></label>
          </div>
          <div className="row">
            <label>Provider model<input name="model" placeholder="musetalk / wav2lip" /></label>
            <label>Quality<select name="quality" defaultValue="production"><option value="preview">Preview</option><option value="production">Production</option><option value="high">High</option></select></label>
          </div>
          <label><input name="preserveAudio" type="checkbox" /> Preserve source clip audio beneath dialogue</label>
          <textarea name="constraints" placeholder="Face and dialogue constraints — one per line" />
          <button type="submit" disabled={!directionId}>Validate timeline and queue</button>
          {!health?.available && <p className="warning">Jobs remain stored while the lip-sync GPU is offline and can be retried later.</p>}
        </form>

        <aside>
          <p className="eyebrow">LIP-SYNC SHOTS</p>
          {jobs.length === 0 && <p className="muted">No lip-sync shots for this series yet.</p>}
          {jobs.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">SC {job.spec.generation.scene_number} · SH {job.spec.generation.shot_number}</span>
                <small>{job.status} · {job.review_status} · attempt {job.attempts}</small>
              </div>
              <p>{job.spec.generation.duration_seconds}s · {job.spec.generation.segments.length} dialogue segment(s) · {job.spec.generation.quality}</p>
              <div className="timeline-list">
                {job.spec.generation.segments.map((segment) => (
                  <div className="timeline-line" key={`${job.id}-${segment.dialogue_order}`}>
                    <strong>{segment.character_name}</strong>
                    <small>{segment.start_time_seconds.toFixed(2)}s → {segment.end_time_seconds.toFixed(2)}s</small>
                    <p>{segment.text}</p>
                  </div>
                ))}
              </div>
              {job.error && <p className="error">{job.error}</p>}
              {job.videos.map((video, index) => (
                <div className="video-result" key={`${job.id}-${index}`}>
                  <video controls preload="metadata" src={artifactUrl(video.url)} />
                  <small>{video.filename} · {video.size_bytes ? `${Math.round(video.size_bytes / 1024)} KB` : "stored"}</small>
                  {video.checksum_sha256 && <code>{video.checksum_sha256.slice(0, 20)}…</code>}
                </div>
              ))}
              {job.status === "failed" && <button className="secondary" type="button" onClick={() => action(`/api/v1/lip-sync-jobs/${job.id}/retry`, "Lip-sync shot queued again.")}>Retry</button>}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/lip-sync-jobs/${job.id}/review`, "Lip-sync shot approved.", { decision: "approved", notes: "Dialogue placement and mouth movement approved." })}>Approve shot</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/lip-sync-jobs/${job.id}/review`, "Changes requested.", { decision: "changes_requested", notes: "Correct face tracking or dialogue timing without changing approved sources." })}>Request changes</button>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
