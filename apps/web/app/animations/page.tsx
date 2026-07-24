"use client";

import { FormEvent, useEffect, useState } from "react";

type JobStatus = "planned" | "queued" | "running" | "succeeded" | "failed";
type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type Series = { id: string; name: string };
type DirectionJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  review_status: ReviewStatus;
  result: null | { title: string; total_estimated_duration_seconds: number; scenes: unknown[] };
};
type AnimationJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    scene_number: number;
    shot_number: number;
    generation: {
      duration_seconds: number;
      fps: number;
      frame_count?: number;
      motion_strength: number;
      prompt: string;
    };
  };
  videos: Array<{
    url: string;
    filename: string;
    size_bytes: number | null;
    checksum_sha256: string;
  }>;
};
type VideoHealth = { available: boolean; provider: string; detail: string };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function artifactUrl(url: string) {
  return url.startsWith("/") ? `${apiUrl}${url}` : url;
}

export default function AnimationsPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [directionId, setDirectionId] = useState("");
  const [jobs, setJobs] = useState<AnimationJob[]>([]);
  const [health, setHealth] = useState<VideoHealth | null>(null);
  const [message, setMessage] = useState("Approve keyframes before creating animated shots.");
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
    const timer = window.setInterval(() => void loadAnimations(seriesId), 4000);
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
    const response = await fetch(`${apiUrl}/api/v1/video/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as VideoHealth);
  }

  async function loadAnimations(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/animation-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setJobs((await response.json()) as AnimationJob[]);
  }

  async function loadProduction(id: string) {
    const [directionResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/direction-jobs`, { cache: "no-store" }),
      loadAnimations(id),
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
    if (!response.ok) return setMessage(data.detail ?? "Animation action failed.");
    setMessage(success);
    if (seriesId) await loadAnimations(seriesId);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!directionId) return;
    const form = new FormData(event.currentTarget);
    await action(
      `/api/v1/direction-jobs/${directionId}/animation-jobs/plan`,
      "Animated shot jobs were planned and queued.",
      {
        fps: Number(form.get("fps") ?? 16),
        max_clip_duration_seconds: Number(form.get("maxDuration") ?? 12),
        motion_strength: Number(form.get("motionStrength") ?? 0.55),
        steps: Number(form.get("steps") ?? 25),
        guidance_scale: Number(form.get("guidance") ?? 3),
        constraints: String(form.get("constraints") ?? "").split("\n").filter(Boolean),
      },
    );
  }

  return (
    <main>
      <header>
        <p className="eyebrow">06 · ANIMATED SHOT PRODUCTION</p>
        <h1>Animation</h1>
        <p className="lede">
          Convert approved keyframes into independent, reviewable video clips. Every result is copied
          from the temporary GPU worker into permanent project storage.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "VIDEO GPU ONLINE" : "VIDEO GPU OFFLINE"}
          </span>
          <small>{health?.detail ?? "Checking ComfyUI video worker..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <form onSubmit={createPlan}>
          <p className="eyebrow">ANIMATION PLAN</p>
          <h2>Queue approved shots</h2>
          <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)} required>
            <option value="">Select series</option>
            {series.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
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
            <label>FPS<input name="fps" type="number" min={4} max={60} defaultValue={16} /></label>
            <label>Maximum clip seconds<input name="maxDuration" type="number" min={1} max={30} step="0.5" defaultValue={12} /></label>
          </div>
          <div className="row">
            <label>Motion strength<input name="motionStrength" type="number" min={0} max={1} step="0.05" defaultValue={0.55} /></label>
            <label>Sampling steps<input name="steps" type="number" min={1} max={150} defaultValue={25} /></label>
          </div>
          <input name="guidance" type="number" min={0} max={30} step="0.1" defaultValue={3} />
          <textarea name="constraints" placeholder="Animation constraints — one per line" />
          <button type="submit" disabled={!directionId}>Plan and queue animations</button>
          {!health?.available && (
            <p className="warning">
              Jobs remain recoverable while the GPU is offline, but clips cannot complete until the
              ComfyUI video workflow is running.
            </p>
          )}
        </form>

        <aside>
          <p className="eyebrow">SHOT QUEUE</p>
          {jobs.length === 0 && <p className="muted">No animated shots for this series yet.</p>}
          {jobs.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">SC {job.spec.scene_number} · SH {job.spec.shot_number}</span>
                <small>{job.status} · {job.review_status} · attempt {job.attempts}</small>
              </div>
              <p>
                {job.spec.generation.duration_seconds}s · {job.spec.generation.fps} fps · motion {job.spec.generation.motion_strength}
              </p>
              {job.error && <p className="error">{job.error}</p>}
              {job.videos.map((video, index) => (
                <div className="video-result" key={`${job.id}-${index}`}>
                  <video controls preload="metadata" src={artifactUrl(video.url)} />
                  <small>
                    {video.filename} · {video.size_bytes ? `${Math.round(video.size_bytes / 1024)} KB` : "stored"}
                  </small>
                  {video.checksum_sha256 && <code>{video.checksum_sha256.slice(0, 20)}…</code>}
                </div>
              ))}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => action(`/api/v1/animation-jobs/${job.id}/retry`, "Animated shot queued again.")}>Retry</button>
              )}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/animation-jobs/${job.id}/review`, "Animated shot approved.", { decision: "approved", notes: "Approved for voice and lip sync." })}>Approve clip</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/animation-jobs/${job.id}/review`, "Changes requested.", { decision: "changes_requested", notes: "Regenerate motion while preserving the approved keyframe." })}>Request changes</button>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
