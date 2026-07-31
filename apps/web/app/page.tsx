"use client";

import { FormEvent, useEffect, useState } from "react";

type Series = {
  id: string;
  name: string;
  logline: string;
  genre: string;
  target_audience: string;
  primary_language: string;
};

type Character = { id: string; name: string; role: string; description: string };

type LlmHealth = {
  available: boolean;
  provider: string;
  model: string;
  detail: string;
};

type EpisodeStory = {
  title: string;
  logline: string;
  theme: string;
  hook: string;
  synopsis: string;
  ending: string;
  scenes: Array<{
    number: number;
    title: string;
    location: string;
    estimated_duration_seconds: number;
  }>;
};

type StoryJob = {
  id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  attempts: number;
  model: string;
  request: { premise: string; target_duration_seconds: number; tone: string };
  result: EpisodeStory | null;
  error: string | null;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [storyJobs, setStoryJobs] = useState<StoryJob[]>([]);
  const [llmHealth, setLlmHealth] = useState<LlmHealth | null>(null);
  const [message, setMessage] = useState("Ready to create the first production bible.");
  const hasActiveJobs = storyJobs.some(
    (job) => job.status === "queued" || job.status === "running",
  );

  useEffect(() => {
    void refreshSeries();
    void refreshLlmHealth();
  }, []);

  useEffect(() => {
    if (!seriesId) {
      setCharacters([]);
      setStoryJobs([]);
      return;
    }
    void refreshCharacters(seriesId);
    void refreshStoryJobs(seriesId);
  }, [seriesId]);

  useEffect(() => {
    if (!seriesId || !hasActiveJobs) return;
    const timer = window.setInterval(() => void refreshStoryJobs(seriesId), 3000);
    return () => window.clearInterval(timer);
  }, [hasActiveJobs, seriesId]);

  async function refreshSeries() {
    const response = await fetch(`${apiUrl}/api/v1/series`, { cache: "no-store" });
    if (!response.ok) return;
    const result = (await response.json()) as Series[];
    setSeries(result);
    setSeriesId((current) => current || result[0]?.id || "");
  }

  async function refreshCharacters(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/characters`, {
      cache: "no-store",
    });
    if (response.ok) setCharacters((await response.json()) as Character[]);
  }

  async function refreshStoryJobs(id: string) {
    const response = await fetch(`${apiUrl}/api/v1/series/${id}/story-jobs`, {
      cache: "no-store",
    });
    if (response.ok) setStoryJobs((await response.json()) as StoryJob[]);
  }

  async function refreshLlmHealth() {
    const response = await fetch(`${apiUrl}/api/v1/llm/health`, { cache: "no-store" });
    if (response.ok) setLlmHealth((await response.json()) as LlmHealth);
  }

  async function createSeries(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/api/v1/series`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        logline: form.get("logline"),
        synopsis: form.get("synopsis"),
        genre: form.get("genre"),
        target_audience: form.get("audience"),
        primary_language: form.get("language"),
        visual_style: {
          art_direction: form.get("artDirection"),
          medium: "2d animation",
          palette: [],
          line_style: "clean production lines",
          lighting: "cinematic",
          aspect_ratio: "16:9",
        },
        rules: {
          world_rules: String(form.get("worldRules") ?? "")
            .split("\n")
            .filter(Boolean),
          prohibited_topics: [],
          continuity_notes: [],
        },
      }),
    });
    const body = await response.json();
    if (!response.ok) return setMessage(body.detail ?? "Could not create series.");
    setMessage(`Series “${body.name}” saved.`);
    event.currentTarget.reset();
    await refreshSeries();
    setSeriesId(body.id);
  }

  async function createCharacter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!seriesId) return;
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/api/v1/series/${seriesId}/characters`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        role: form.get("role"),
        description: form.get("description"),
        personality_traits: String(form.get("traits") ?? "").split(",").filter(Boolean),
        visual_identity: {
          reference_prompt: form.get("referencePrompt"),
          palette: [],
          signature_features: String(form.get("features") ?? "").split(",").filter(Boolean),
        },
        wardrobe: { default: String(form.get("wardrobe") ?? "") },
        speaking_style: form.get("speakingStyle"),
        voice_profile: { language: "en", description: form.get("voice") },
      }),
    });
    const body = await response.json();
    if (!response.ok) return setMessage(body.detail ?? "Could not create character.");
    setMessage(`Character “${body.name}” saved with a permanent identity.`);
    event.currentTarget.reset();
    await refreshCharacters(seriesId);
  }

  async function createStory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!seriesId) return;
    const form = new FormData(event.currentTarget);
    const response = await fetch(`${apiUrl}/api/v1/series/${seriesId}/story-jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        premise: form.get("premise"),
        target_duration_seconds: Number(form.get("duration") ?? 300),
        tone: form.get("tone"),
        constraints: String(form.get("constraints") ?? "")
          .split("\n")
          .filter(Boolean),
      }),
    });
    const body = await response.json();
    if (!response.ok) return setMessage(body.detail ?? "Could not queue story generation.");
    setMessage(`Story job queued on ${body.model}.`);
    event.currentTarget.reset();
    await refreshStoryJobs(seriesId);
  }

  async function retryStory(jobId: string) {
    const response = await fetch(`${apiUrl}/api/v1/story-jobs/${jobId}/retry`, {
      method: "POST",
    });
    const body = await response.json();
    if (!response.ok) return setMessage(body.detail ?? "Could not retry story generation.");
    setMessage("Story job queued again.");
    if (seriesId) await refreshStoryJobs(seriesId);
  }

  return (
    <main>
      <header>
        <p className="eyebrow">AI CARTOON PRODUCTION CONTROL</p>
        <h1>Series Bible</h1>
        <p className="lede">
          Permanent worlds and character identities that every future story, shot, voice, and
          render must follow.
        </p>
        <div className="health-row">
          <span className={llmHealth?.available ? "health online" : "health offline"}>
            {llmHealth?.available ? "LOCAL LLM ONLINE" : "LOCAL LLM OFFLINE"}
          </span>
          <small>{llmHealth?.model ?? "Checking self-hosted model..."}</small>
          <button className="secondary compact" type="button" onClick={refreshLlmHealth}>
            Check again
          </button>
        </div>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <form onSubmit={createSeries}>
          <p className="eyebrow">01 · WORLD</p>
          <h2>Create a series</h2>
          <input name="name" required minLength={2} placeholder="Series name" />
          <textarea name="logline" required minLength={10} placeholder="Logline" />
          <textarea name="synopsis" placeholder="Long-term synopsis" />
          <div className="row">
            <input name="genre" required placeholder="Genre" />
            <input name="audience" required placeholder="Audience" />
          </div>
          <input name="language" defaultValue="en" required placeholder="Language" />
          <textarea name="artDirection" required minLength={3} placeholder="Art direction" />
          <textarea name="worldRules" placeholder="World rules — one per line" />
          <button type="submit">Save series bible</button>
        </form>

        <aside>
          <p className="eyebrow">SERIES LIBRARY</p>
          {series.map((item) => (
            <button
              className={item.id === seriesId ? "card active" : "card"}
              key={item.id}
              type="button"
              onClick={() => setSeriesId(item.id)}
            >
              <strong>{item.name}</strong>
              <span>{item.logline}</span>
              <small>
                {item.genre} · {item.target_audience}
              </small>
            </button>
          ))}
        </aside>
      </section>

      <section className="workspace">
        <form onSubmit={createCharacter}>
          <p className="eyebrow">02 · IDENTITY</p>
          <h2>Create a character</h2>
          <fieldset disabled={!seriesId}>
            <input name="name" required minLength={2} placeholder="Character name" />
            <select name="role" defaultValue="protagonist">
              <option value="protagonist">Protagonist</option>
              <option value="deuteragonist">Deuteragonist</option>
              <option value="supporting">Supporting</option>
              <option value="antagonist">Antagonist</option>
              <option value="recurring">Recurring</option>
            </select>
            <textarea name="description" required minLength={10} placeholder="Description" />
            <input name="traits" placeholder="Traits, comma separated" />
            <textarea
              name="referencePrompt"
              required
              minLength={10}
              placeholder="Permanent visual reference prompt"
            />
            <input name="features" placeholder="Signature features" />
            <input name="wardrobe" placeholder="Default wardrobe" />
            <textarea name="speakingStyle" placeholder="Speaking style" />
            <textarea name="voice" placeholder="Voice identity" />
            <button type="submit">Save character identity</button>
          </fieldset>
        </form>

        <aside>
          <p className="eyebrow">CHARACTER REGISTRY</p>
          {characters.map((character) => (
            <article className="character" key={character.id}>
              <small>{character.role}</small>
              <h3>{character.name}</h3>
              <p>{character.description}</p>
            </article>
          ))}
        </aside>
      </section>

      <section className="workspace">
        <form onSubmit={createStory}>
          <p className="eyebrow">03 · STORY ENGINE</p>
          <h2>Generate an episode story</h2>
          <fieldset disabled={!seriesId}>
            <textarea
              name="premise"
              required
              minLength={10}
              placeholder="Episode premise or central problem"
            />
            <div className="row">
              <input name="duration" type="number" min={60} max={3600} defaultValue={300} />
              <input name="tone" required defaultValue="adventurous and emotionally warm" />
            </div>
            <textarea name="constraints" placeholder="Episode constraints — one per line" />
            <button type="submit">Queue story generation</button>
          </fieldset>
          {!llmHealth?.available && (
            <p className="warning">
              The job will remain recoverable, but start the Lightning or Colab LLM worker before
              expecting a completed story.
            </p>
          )}
        </form>

        <aside>
          <p className="eyebrow">STORY JOBS</p>
          {storyJobs.length === 0 && <p className="muted">No story jobs for this series yet.</p>}
          {storyJobs.map((job) => (
            <article className={`job ${job.status}`} key={job.id}>
              <div className="job-head">
                <span className="status">{job.status}</span>
                <small>Attempt {job.attempts}</small>
              </div>
              <p>{job.request.premise}</p>
              {job.error && <p className="error">{job.error}</p>}
              {job.status === "failed" && (
                <button className="secondary" type="button" onClick={() => retryStory(job.id)}>
                  Retry job
                </button>
              )}
              {job.result && (
                <div className="story-result">
                  <h3>{job.result.title}</h3>
                  <strong>{job.result.logline}</strong>
                  <p>{job.result.synopsis}</p>
                  <small>
                    {job.result.scenes.length} scenes · {job.result.theme}
                  </small>
                </div>
              )}
            </article>
          ))}
        </aside>
      </section>
    </main>
  );
}
