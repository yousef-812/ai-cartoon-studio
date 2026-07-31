"use client";

import { FormEvent, useEffect, useState } from "react";

type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type JobStatus = "queued" | "running" | "succeeded" | "failed";
type Series = { id: string; name: string; logline: string };
type StoryJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  request: { premise: string; target_duration_seconds: number };
  result: null | { title: string; logline: string; synopsis: string; scenes: unknown[] };
  error: string | null;
};
type ScriptJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  result: null | {
    title: string;
    total_estimated_duration_seconds: number;
    scenes: Array<{
      number: number;
      title: string;
      location: string;
      dialogue: Array<{ speaker: string; text: string; emotion: string }>;
    }>;
  };
  error: string | null;
};
type LlmHealth = { available: boolean; model: string; detail: string };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ProductionPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [stories, setStories] = useState<StoryJob[]>([]);
  const [scripts, setScripts] = useState<ScriptJob[]>([]);
  const [health, setHealth] = useState<LlmHealth | null>(null);
  const [message, setMessage] = useState("Select a series and start production.");
  const active = [...stories, ...scripts].some(
    (job) => job.status === "queued" || job.status === "running",
  );

  useEffect(() => {
    void loadSeries();
    void loadHealth();
  }, []);

  useEffect(() => {
    if (seriesId) void loadJobs(seriesId);
  }, [seriesId]);

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
    setSeriesId((current) => current || data[0]?.id || "");
  }

  async function loadHealth() {
    const response = await fetch(`${apiUrl}/api/v1/llm/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as LlmHealth);
  }

  async function loadJobs(id: string) {
    const [storyResponse, scriptResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/story-jobs`, { cache: "no-store" }),
      fetch(`${apiUrl}/api/v1/series/${id}/script-jobs`, { cache: "no-store" }),
    ]);
    if (storyResponse.ok) setStories((await storyResponse.json()) as StoryJob[]);
    if (scriptResponse.ok) setScripts((await scriptResponse.json()) as ScriptJob[]);
  }

  async function action(path: string, success: string, body?: object) {
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Production action failed.");
    setMessage(success);
    if (seriesId) await loadJobs(seriesId);
  }

  async function createStory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!seriesId) return;
    const form = new FormData(event.currentTarget);
    await action(`/api/v1/series/${seriesId}/story-jobs`, "Story generation queued.", {
      premise: form.get("premise"),
      target_duration_seconds: Number(form.get("duration") ?? 300),
      tone: form.get("tone"),
      constraints: String(form.get("constraints") ?? "").split("\n").filter(Boolean),
    });
    event.currentTarget.reset();
  }

  return (
    <main>
      <header>
        <p className="eyebrow">STORY → SCRIPT → DIRECTION</p>
        <h1>Production</h1>
        <p className="lede">
          Review each AI output before it enters the next production stage. Free GPU sessions can
          disconnect without losing queued work or results.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "LOCAL LLM ONLINE" : "LOCAL LLM OFFLINE"}
          </span>
          <small>{health?.model ?? "Checking model..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <form onSubmit={createStory}>
          <p className="eyebrow">03 · STORY</p>
          <h2>Generate episode story</h2>
          <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)} required>
            <option value="">Select series</option>
            {series.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
          <textarea name="premise" required minLength={10} placeholder="Episode premise" />
          <div className="row">
            <input name="duration" type="number" min={60} max={3600} defaultValue={300} />
            <input name="tone" defaultValue="adventurous and emotionally warm" required />
          </div>
          <textarea name="constraints" placeholder="Constraints — one per line" />
          <button type="submit" disabled={!seriesId}>Queue story</button>
        </form>
        <aside>
          <p className="eyebrow">STORY REVIEW</p>
          {stories.length === 0 && <p className="muted">No story jobs yet.</p>}
          {stories.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">{job.status}</span>
                <small>{job.review_status} · attempt {job.attempts}</small>
              </div>
              <p>{job.request.premise}</p>
              {job.error && <p className="error">{job.error}</p>}
              {job.result && (
                <div className="story-result">
                  <h3>{job.result.title}</h3>
                  <strong>{job.result.logline}</strong>
                  <p>{job.result.synopsis}</p>
                  <small>{job.result.scenes.length} scenes</small>
                </div>
              )}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => action(`/api/v1/story-jobs/${job.id}/retry`, "Story queued again.")}>Retry</button>
              )}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/story-jobs/${job.id}/review`, "Story approved.", { decision: "approved", notes: "Approved for screenplay." })}>Approve story</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/story-jobs/${job.id}/review`, "Story returned for changes.", { decision: "changes_requested", notes: "Revise the story before scripting." })}>Request changes</button>
                </div>
              )}
              {job.review_status === "approved" && (
                <button type="button" onClick={() => action(`/api/v1/story-jobs/${job.id}/script-jobs`, "Screenplay queued.", { dialogue_style: "natural, character-specific, emotionally clear, and concise", pacing: "cinematic with escalating conflict and a clean resolution" })}>Generate screenplay</button>
              )}
            </article>
          ))}
        </aside>
      </section>

      <section className="workspace full">
        <div className="panel">
          <p className="eyebrow">04 · SCRIPT & DIALOGUE</p>
          <h2>Screenplay review</h2>
          <p className="muted">Dialogue speakers must match the permanent character registry.</p>
        </div>
        <aside>
          {scripts.length === 0 && <p className="muted">No screenplay jobs yet.</p>}
          {scripts.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">{job.status}</span>
                <small>{job.review_status} · attempt {job.attempts}</small>
              </div>
              {job.error && <p className="error">{job.error}</p>}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => action(`/api/v1/script-jobs/${job.id}/retry`, "Screenplay queued again.")}>Retry</button>
              )}
              {job.result && (
                <div className="script-result">
                  <h3>{job.result.title}</h3>
                  <p>{job.result.scenes.length} scenes · {job.result.total_estimated_duration_seconds}s</p>
                  {job.result.scenes.map((scene) => (
                    <div className="scene" key={scene.number}>
                      <strong>{scene.number}. {scene.title}</strong>
                      <small>{scene.location} · {scene.dialogue.length} lines</small>
                      {scene.dialogue.slice(0, 2).map((line, index) => (
                        <p key={`${scene.number}-${index}`}><b>{line.speaker}:</b> {line.text} <em>({line.emotion})</em></p>
                      ))}
                    </div>
                  ))}
                </div>
              )}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/script-jobs/${job.id}/review`, "Screenplay approved for directing.", { decision: "approved", notes: "Approved for directing." })}>Approve screenplay</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/script-jobs/${job.id}/review`, "Screenplay returned for changes.", { decision: "changes_requested", notes: "Revise dialogue and pacing." })}>Request changes</button>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
