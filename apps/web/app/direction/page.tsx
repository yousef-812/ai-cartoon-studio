"use client";

import { useEffect, useState } from "react";

type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type JobStatus = "queued" | "running" | "succeeded" | "failed";
type Series = { id: string; name: string };
type ScriptJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  result: null | { title: string; scenes: unknown[]; total_estimated_duration_seconds: number };
};
type DirectionJob = {
  id: string;
  script_job_id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  result: null | {
    title: string;
    total_estimated_duration_seconds: number;
    scenes: Array<{
      scene_number: number;
      title: string;
      shots: Array<{
        number: number;
        duration_seconds: number;
        shot_size: string;
        camera_movement: string;
        action: string;
        characters: string[];
      }>;
    }>;
  };
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function DirectionPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [scripts, setScripts] = useState<ScriptJob[]>([]);
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [message, setMessage] = useState("Approve a screenplay, then create its shot plan.");
  const active = directions.some((job) => job.status === "queued" || job.status === "running");

  useEffect(() => { void loadSeries(); }, []);
  useEffect(() => { if (seriesId) void loadJobs(seriesId); }, [seriesId]);
  useEffect(() => {
    if (!seriesId || !active) return;
    const timer = window.setInterval(() => void loadJobs(seriesId), 3000);
    return () => window.clearInterval(timer);
  }, [active, seriesId]);

  async function loadSeries() {
    const response = await fetch(`${apiUrl}/api/v1/series`, { cache: "no-store" });
    if (!response.ok) return;
    const data = (await response.json()) as Series[];
    setSeries(data);
    setSeriesId(data[0]?.id ?? "");
  }

  async function loadJobs(id: string) {
    const [scriptsResponse, directionsResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/script-jobs`, { cache: "no-store" }),
      fetch(`${apiUrl}/api/v1/series/${id}/direction-jobs`, { cache: "no-store" }),
    ]);
    if (scriptsResponse.ok) setScripts((await scriptsResponse.json()) as ScriptJob[]);
    if (directionsResponse.ok) setDirections((await directionsResponse.json()) as DirectionJob[]);
  }

  async function action(path: string, success: string, body?: object) {
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Direction action failed.");
    setMessage(success);
    if (seriesId) await loadJobs(seriesId);
  }

  const approvedScripts = scripts.filter(
    (job) => job.status === "succeeded" && job.review_status === "approved" && job.result,
  );

  return (
    <main>
      <header>
        <p className="eyebrow">05 · DIRECTOR & SHOT BREAKDOWN</p>
        <h1>Direction</h1>
        <p className="lede">
          Convert approved screenplay scenes into timed, continuity-safe shots before generating a
          single image or video frame.
        </p>
        <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)}>
          <option value="">Select series</option>
          {series.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <div className="panel">
          <p className="eyebrow">APPROVED SCREENPLAYS</p>
          <h2>Start directing</h2>
          {approvedScripts.length === 0 && <p className="muted">Approve a screenplay on the production page first.</p>}
          {approvedScripts.map((job) => (
            <article className="job succeeded" key={job.id}>
              <h3>{job.result?.title}</h3>
              <p>{job.result?.scenes.length} scenes · {job.result?.total_estimated_duration_seconds}s</p>
              <button type="button" onClick={() => action(`/api/v1/script-jobs/${job.id}/direction-jobs`, "Direction job queued.", { max_shot_duration_seconds: 8, directing_style: "cinematic, readable, emotionally motivated, and animation-efficient" })}>Generate shot plan</button>
            </article>
          ))}
        </div>
        <aside>
          <p className="eyebrow">DIRECTION JOBS</p>
          {directions.length === 0 && <p className="muted">No shot plans yet.</p>}
          {directions.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head"><span className="status">{job.status}</span><small>{job.review_status} · attempt {job.attempts}</small></div>
              {job.error && <p className="error">{job.error}</p>}
              {job.status === "failed" && <button className="secondary" type="button" onClick={() => action(`/api/v1/direction-jobs/${job.id}/retry`, "Direction job queued again.")}>Retry</button>}
              {job.result && <div className="script-result"><h3>{job.result.title}</h3><p>{job.result.scenes.reduce((count, scene) => count + scene.shots.length, 0)} shots · {job.result.total_estimated_duration_seconds}s</p>{job.result.scenes.map((scene) => <div className="scene" key={scene.scene_number}><strong>Scene {scene.scene_number}: {scene.title}</strong><small>{scene.shots.length} shots</small>{scene.shots.slice(0, 3).map((shot) => <p key={shot.number}><b>{shot.number}. {shot.shot_size}</b> · {shot.duration_seconds}s · {shot.camera_movement}<br />{shot.action}</p>)}</div>)}</div>}
              {job.status === "succeeded" && <div className="actions"><button type="button" onClick={() => action(`/api/v1/direction-jobs/${job.id}/review`, "Shot plan approved for visual production.", { decision: "approved", notes: "Approved for visual production." })}>Approve direction</button><button className="secondary" type="button" onClick={() => action(`/api/v1/direction-jobs/${job.id}/review`, "Shot plan returned for changes.", { decision: "changes_requested", notes: "Revise shot timing and composition." })}>Request changes</button></div>}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
