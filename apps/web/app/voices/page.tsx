"use client";

import { FormEvent, useEffect, useState } from "react";

type JobStatus = "planned" | "queued" | "running" | "succeeded" | "failed";
type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type Series = { id: string; name: string };
type VoiceProfile = {
  provider: string;
  voice_id: string;
  language: string;
  description: string;
  speed: number;
  pitch: number;
};
type Character = {
  id: string;
  name: string;
  role: string;
  voice_profile: VoiceProfile;
};
type ScriptJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  review_status: ReviewStatus;
  result: null | { title: string; scenes: Array<{ dialogue: unknown[] }> };
};
type VoiceJob = {
  id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    scene_number: number;
    dialogue_order: number;
    character_name: string;
    pause_after_ms: number;
    synthesis: {
      text: string;
      voice_id: string;
      emotion: string;
      delivery: string;
      speed: number;
      pitch: number;
      target_duration_seconds: number | null;
    };
  };
  audio: null | {
    url: string;
    filename: string;
    size_bytes: number | null;
    checksum_sha256: string;
    duration_seconds: number | null;
  };
};
type VoiceHealth = { available: boolean; provider: string; model: string; detail: string };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function artifactUrl(url: string) {
  return url.startsWith("/") ? `${apiUrl}${url}` : url;
}

export default function VoicesPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [scripts, setScripts] = useState<ScriptJob[]>([]);
  const [scriptId, setScriptId] = useState("");
  const [jobs, setJobs] = useState<VoiceJob[]>([]);
  const [health, setHealth] = useState<VoiceHealth | null>(null);
  const [message, setMessage] = useState("Assign one permanent voice identity to every speaking character.");
  const active = jobs.some((job) => job.status === "queued" || job.status === "running");

  useEffect(() => {
    void loadSeries();
    void loadHealth();
  }, []);

  useEffect(() => {
    if (seriesId) void loadProduction(seriesId);
  }, [seriesId]);

  useEffect(() => {
    if (!seriesId || !active) return;
    const timer = window.setInterval(() => void loadVoiceJobs(seriesId), 3000);
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
    const response = await fetch(`${apiUrl}/api/v1/voice/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as VoiceHealth);
  }

  async function loadVoiceJobs(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/voice-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setJobs((await response.json()) as VoiceJob[]);
  }

  async function loadProduction(id: string) {
    const [characterResponse, scriptResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/characters`, { cache: "no-store" }),
      fetch(`${apiUrl}/api/v1/series/${id}/script-jobs`, { cache: "no-store" }),
      loadVoiceJobs(id),
    ]);
    if (characterResponse.ok) setCharacters((await characterResponse.json()) as Character[]);
    if (scriptResponse.ok) {
      const data = (await scriptResponse.json()) as ScriptJob[];
      const approved = data.filter(
        (job) => job.status === "succeeded" && job.review_status === "approved" && job.result,
      );
      setScripts(approved);
      setScriptId((current) =>
        approved.some((job) => job.id === current) ? current : approved[0]?.id || "",
      );
    }
  }

  async function action(path: string, success: string, body?: object) {
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Voice production action failed.");
    setMessage(success);
    if (seriesId) await loadVoiceJobs(seriesId);
  }

  async function saveVoice(event: FormEvent<HTMLFormElement>, character: Character) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/api/v1/characters/${character.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_profile: {
          provider: form.get("provider"),
          voice_id: form.get("voiceId"),
          language: form.get("language"),
          description: form.get("description"),
          speed: Number(form.get("speed") ?? 1),
          pitch: Number(form.get("pitch") ?? 1),
        },
      }),
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Could not save voice identity.");
    setMessage(`Permanent voice saved for ${character.name}.`);
    if (seriesId) await loadProduction(seriesId);
  }

  async function createPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!scriptId) return;
    const form = new FormData(event.currentTarget);
    await action(`/api/v1/script-jobs/${scriptId}/voice-jobs/plan`, "Voice lines queued.", {
      response_format: form.get("format"),
      model: form.get("model"),
      global_speed_multiplier: Number(form.get("speedMultiplier") ?? 1),
      constraints: String(form.get("constraints") ?? "").split("\n").filter(Boolean),
    });
  }

  return (
    <main>
      <header>
        <p className="eyebrow">07 · VOICE ACTING</p>
        <h1>Voices</h1>
        <p className="lede">
          Preserve a permanent voice identity for every character, then synthesize each approved
          screenplay line with its emotion, delivery, speed, pitch, and timing metadata.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "VOICE ENGINE ONLINE" : "VOICE ENGINE OFFLINE"}
          </span>
          <small>{health?.model || health?.detail || "Checking self-hosted TTS..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="asset-section">
        <div className="asset-heading">
          <div>
            <p className="eyebrow">PERMANENT VOICE REGISTRY</p>
            <h2>Character voices</h2>
          </div>
          <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)}>
            <option value="">Select series</option>
            {series.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </div>
        <div className="asset-grid">
          {characters.map((character) => (
            <form className="asset-card" key={character.id} onSubmit={(event) => saveVoice(event, character)}>
              <div className="asset-body">
                <small>{character.role}</small>
                <h3>{character.name}</h3>
                <input name="provider" defaultValue={character.voice_profile.provider || "local-openai-compatible-tts"} placeholder="Provider" />
                <input name="voiceId" required defaultValue={character.voice_profile.voice_id} placeholder="Permanent voice ID" />
                <input name="language" required defaultValue={character.voice_profile.language || "en"} placeholder="Language" />
                <textarea name="description" defaultValue={character.voice_profile.description} placeholder="Voice identity description" />
                <div className="row">
                  <label>Speed<input name="speed" type="number" min={0.5} max={2} step="0.05" defaultValue={character.voice_profile.speed || 1} /></label>
                  <label>Pitch<input name="pitch" type="number" min={0.5} max={2} step="0.05" defaultValue={character.voice_profile.pitch || 1} /></label>
                </div>
                <button type="submit">Save permanent voice</button>
              </div>
            </form>
          ))}
        </div>
      </section>

      <section className="workspace">
        <form onSubmit={createPlan}>
          <p className="eyebrow">VOICE PLAN</p>
          <h2>Synthesize screenplay dialogue</h2>
          <select value={scriptId} onChange={(event) => setScriptId(event.target.value)} required>
            <option value="">Select approved screenplay</option>
            {scripts.map((job) => (
              <option key={job.id} value={job.id}>{job.result?.title ?? job.id}</option>
            ))}
          </select>
          <div className="row">
            <select name="format" defaultValue="wav">
              <option value="wav">WAV</option>
              <option value="mp3">MP3</option>
              <option value="flac">FLAC</option>
              <option value="opus">Opus</option>
            </select>
            <input name="model" placeholder="Provider model override" />
          </div>
          <label>Global speed multiplier<input name="speedMultiplier" type="number" min={0.5} max={2} step="0.05" defaultValue={1} /></label>
          <textarea name="constraints" placeholder="Voice direction constraints — one per line" />
          <button type="submit" disabled={!scriptId}>Plan and queue voice lines</button>
          {!health?.available && (
            <p className="warning">
              Voice jobs remain saved while the TTS server is offline and can be retried later.
            </p>
          )}
        </form>

        <aside>
          <p className="eyebrow">DIALOGUE REVIEW</p>
          {jobs.length === 0 && <p className="muted">No generated voice lines yet.</p>}
          {jobs.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">SC {job.spec.scene_number} · LINE {job.spec.dialogue_order}</span>
                <small>{job.status} · {job.review_status} · attempt {job.attempts}</small>
              </div>
              <strong>{job.spec.character_name}</strong>
              <p>{job.spec.synthesis.text}</p>
              <small>{job.spec.synthesis.emotion} · {job.spec.synthesis.delivery}</small>
              {job.error && <p className="error">{job.error}</p>}
              {job.audio && (
                <div className="audio-result">
                  <audio controls preload="metadata" src={artifactUrl(job.audio.url)} />
                  <small>
                    {job.audio.filename} · {job.audio.duration_seconds ?? "?"}s · pause {job.spec.pause_after_ms}ms
                  </small>
                  {job.audio.checksum_sha256 && <code>{job.audio.checksum_sha256.slice(0, 20)}…</code>}
                </div>
              )}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => action(`/api/v1/voice-jobs/${job.id}/retry`, "Voice line queued again.")}>Retry</button>
              )}
              {job.status === "succeeded" && (
                <div className="actions">
                  <button type="button" onClick={() => action(`/api/v1/voice-jobs/${job.id}/review`, "Voice line approved.", { decision: "approved", notes: "Approved for lip sync." })}>Approve voice</button>
                  <button className="secondary" type="button" onClick={() => action(`/api/v1/voice-jobs/${job.id}/review`, "Voice changes requested.", { decision: "changes_requested", notes: "Regenerate with corrected emotion, delivery, or timing." })}>Request changes</button>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
