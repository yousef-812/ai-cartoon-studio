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
type SoundAsset = {
  cue_key: string;
  kind: "ambience" | "effect" | "music";
  prompt: string;
  url: string;
  filename: string;
  size_bytes: number | null;
  checksum_sha256: string;
};
type SoundJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    source_job_type: "animation" | "lip_sync";
    generation: {
      scene_number: number;
      shot_number: number;
      duration_seconds: number;
      dialogue_ducking_db: number;
      target_loudness_lufs: number;
      cues: Array<{ key: string; kind: string; prompt: string; gain_db: number }>;
    };
  };
  assets: SoundAsset[];
  videos: Array<{
    url: string;
    filename: string;
    size_bytes: number | null;
    checksum_sha256: string;
  }>;
};
type SoundHealth = {
  available: boolean;
  ffmpeg_available: boolean;
  detail: string;
  provider: { available: boolean; provider: string; detail: string };
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function artifactUrl(url: string) {
  return url.startsWith("/") ? `${apiUrl}${url}` : url;
}

export default function SoundDesignPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [directionId, setDirectionId] = useState("");
  const [jobs, setJobs] = useState<SoundJob[]>([]);
  const [health, setHealth] = useState<SoundHealth | null>(null);
  const [message, setMessage] = useState("Approve animation, voices, and lip sync before sound design.");
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
    const response = await fetch(`${apiUrl}/api/v1/sound/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as SoundHealth);
  }

  async function loadJobs(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/sound-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setJobs((await response.json()) as SoundJob[]);
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
    if (!response.ok) return setMessage(data.detail ?? "Sound design action failed.");
    setMessage(success);
    if (seriesId) await loadJobs(seriesId);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!directionId) return;
    const form = new FormData(event.currentTarget);
    await action(
      `/api/v1/direction-jobs/${directionId}/sound-jobs/plan`,
      "Sound assets and shot mixes were planned and queued.",
      {
        include_ambience: form.get("ambience") === "on",
        include_effects: form.get("effects") === "on",
        include_music: form.get("music") === "on",
        ambience_gain_db: Number(form.get("ambienceGain") ?? -20),
        effects_gain_db: Number(form.get("effectsGain") ?? -12),
        music_gain_db: Number(form.get("musicGain") ?? -22),
        dialogue_ducking_db: Number(form.get("ducking") ?? -10),
        target_loudness_lufs: Number(form.get("loudness") ?? -16),
        sound_model: String(form.get("soundModel") ?? ""),
        music_model: String(form.get("musicModel") ?? ""),
        constraints: String(form.get("constraints") ?? "").split("\n").filter(Boolean),
      },
    );
  }

  return (
    <main>
      <header>
        <p className="eyebrow">09 · SOUND DESIGN & MUSIC</p>
        <h1>Sound Mix</h1>
        <p className="lede">
          Generate ambience, visible-action effects, and instrumental score for each approved shot,
          then mix them with dialogue using ducking and loudness control.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "SOUND SYSTEM ONLINE" : "SOUND SYSTEM OFFLINE"}
          </span>
          <small>{health?.detail ?? "Checking sound provider and FFmpeg..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace full">
        <form onSubmit={createPlan}>
          <p className="eyebrow">SHOT MIX PLAN</p>
          <h2>Design the soundtrack</h2>
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
            <label><input name="ambience" type="checkbox" defaultChecked /> Ambience</label>
            <label><input name="effects" type="checkbox" defaultChecked /> Effects</label>
          </div>
          <label><input name="music" type="checkbox" defaultChecked /> Instrumental music</label>
          <div className="row">
            <label>Ambience gain dB<input name="ambienceGain" type="number" min={-60} max={6} step="1" defaultValue={-20} /></label>
            <label>Effects gain dB<input name="effectsGain" type="number" min={-60} max={6} step="1" defaultValue={-12} /></label>
          </div>
          <div className="row">
            <label>Music gain dB<input name="musicGain" type="number" min={-60} max={6} step="1" defaultValue={-22} /></label>
            <label>Dialogue ducking dB<input name="ducking" type="number" min={-40} max={0} step="1" defaultValue={-10} /></label>
          </div>
          <label>Target loudness LUFS<input name="loudness" type="number" min={-24} max={-5} step="1" defaultValue={-16} /></label>
          <input name="soundModel" placeholder="Sound model override" />
          <input name="musicModel" placeholder="Music model override" />
          <textarea name="constraints" placeholder="Sound constraints — one per line" />
          <button type="submit" disabled={!directionId}>Plan and queue sound mixes</button>
          {!health?.available && (
            <p className="warning">
              Jobs remain recoverable while the provider is offline. Both the sound endpoint and
              FFmpeg must be available for a mix to complete.
            </p>
          )}
        </form>

        <aside>
          <p className="eyebrow">SHOT SOUND QUEUE</p>
          {jobs.length === 0 && <p className="muted">No sound mixes for this series yet.</p>}
          {jobs.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">
                  SC {job.spec.generation.scene_number} · SH {job.spec.generation.shot_number}
                </span>
                <small>{job.status} · {job.review_status} · attempt {job.attempts}</small>
              </div>
              <p>
                {job.spec.source_job_type} source · {job.spec.generation.duration_seconds}s ·
                {" "}{job.spec.generation.target_loudness_lufs} LUFS
              </p>
              <div className="cue-list">
                {job.spec.generation.cues.map((cue) => (
                  <div className="cue" key={cue.key}>
                    <strong>{cue.kind}</strong>
                    <span>{cue.gain_db} dB</span>
                    <small>{cue.prompt}</small>
                  </div>
                ))}
              </div>
              {job.error && <p className="error">{job.error}</p>}
              {job.assets.map((asset) => (
                <div className="audio-result" key={asset.cue_key}>
                  <strong>{asset.kind}</strong>
                  <audio controls preload="metadata" src={artifactUrl(asset.url)} />
                  <small>{asset.filename}</small>
                </div>
              ))}
              {job.videos.map((video) => (
                <div className="video-result" key={video.url}>
                  <video controls preload="metadata" src={artifactUrl(video.url)} />
                  <small>{video.filename}</small>
                  {video.checksum_sha256 && <code>{video.checksum_sha256.slice(0, 20)}…</code>}
                </div>
              ))}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => action(`/api/v1/sound-jobs/${job.id}/retry`, "Sound mix queued again.")}>Retry</button>
              )}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/sound-jobs/${job.id}/review`, "Sound mix approved.", { decision: "approved", notes: "Approved for final episode assembly." })}>Approve mix</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/sound-jobs/${job.id}/review`, "Changes requested.", { decision: "changes_requested", notes: "Revise cue generation, timing, gain, ducking, or loudness." })}>Request changes</button>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
