"use client";

import { useEffect, useMemo, useState } from "react";

type JobStatus = "planned" | "blocked" | "queued" | "running" | "succeeded" | "failed";
type ReviewStatus = "pending_review" | "approved" | "changes_requested";
type Series = { id: string; name: string };
type DirectionJob = {
  id: string;
  status: string;
  review_status: ReviewStatus;
  result: null | { title: string; scenes: unknown[] };
};
type VisualAsset = {
  id: string;
  direction_job_id: string;
  status: JobStatus;
  review_status: ReviewStatus;
  attempts: number;
  error: string | null;
  spec: {
    key: string;
    asset_type: string;
    name: string;
    dependency_keys: string[];
    scene_number: number | null;
    shot_number: number | null;
  };
  images: Array<{ url: string; filename: string }>;
};
type ImageHealth = { available: boolean; provider: string; detail: string };

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function VisualsPage() {
  const [series, setSeries] = useState<Series[]>([]);
  const [seriesId, setSeriesId] = useState("");
  const [directions, setDirections] = useState<DirectionJob[]>([]);
  const [assets, setAssets] = useState<VisualAsset[]>([]);
  const [health, setHealth] = useState<ImageHealth | null>(null);
  const [message, setMessage] = useState("Approve a direction plan before creating visual assets.");
  const active = assets.some((asset) => asset.status === "queued" || asset.status === "running");

  const approvedDirections = directions.filter(
    (job) => job.status === "succeeded" && job.review_status === "approved" && job.result,
  );
  const grouped = useMemo(() => {
    const groups = new Map<string, VisualAsset[]>();
    for (const asset of assets) {
      const items = groups.get(asset.spec.asset_type) ?? [];
      items.push(asset);
      groups.set(asset.spec.asset_type, items);
    }
    return [...groups.entries()];
  }, [assets]);

  useEffect(() => {
    void loadSeries();
    void loadHealth();
  }, []);
  useEffect(() => { if (seriesId) void loadData(seriesId); }, [seriesId]);
  useEffect(() => {
    if (!seriesId || !active) return;
    const timer = window.setInterval(() => void loadData(seriesId), 3000);
    return () => window.clearInterval(timer);
  }, [active, seriesId]);

  async function loadSeries() {
    const response = await fetch(`${apiUrl}/api/v1/series`, { cache: "no-store" });
    if (!response.ok) return;
    const data = (await response.json()) as Series[];
    setSeries(data);
    setSeriesId(data[0]?.id ?? "");
  }

  async function loadHealth() {
    const response = await fetch(`${apiUrl}/api/v1/images/health`, { cache: "no-store" });
    if (response.ok) setHealth((await response.json()) as ImageHealth);
  }

  async function loadData(id: string) {
    const [directionResponse, assetResponse] = await Promise.all([
      fetch(`${apiUrl}/api/v1/series/${id}/direction-jobs`, { cache: "no-store" }),
      fetch(`${apiUrl}/api/v1/series/${id}/visual-assets`, { cache: "no-store" }),
    ]);
    if (directionResponse.ok) setDirections((await directionResponse.json()) as DirectionJob[]);
    if (assetResponse.ok) setAssets((await assetResponse.json()) as VisualAsset[]);
  }

  async function action(path: string, success: string, body?: object) {
    const response = await fetch(`${apiUrl}${path}`, {
      method: "POST",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!response.ok) return setMessage(data.detail ?? "Visual production action failed.");
    setMessage(success);
    if (seriesId) await loadData(seriesId);
  }

  return (
    <main>
      <header>
        <p className="eyebrow">06 · VISUAL ASSET PRODUCTION</p>
        <h1>Visuals</h1>
        <p className="lede">
          Generate permanent character references and backgrounds first. Shot keyframes remain
          blocked until every dependency is reviewed and approved.
        </p>
        <div className="health-row">
          <span className={health?.available ? "health online" : "health offline"}>
            {health?.available ? "COMFYUI ONLINE" : "COMFYUI OFFLINE"}
          </span>
          <small>{health?.detail ?? "Checking image worker..."}</small>
          <button className="secondary compact" type="button" onClick={loadHealth}>Check again</button>
        </div>
        <select value={seriesId} onChange={(event) => setSeriesId(event.target.value)}>
          <option value="">Select series</option>
          {series.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <p className="message">{message}</p>
      </header>

      <section className="workspace">
        <div className="panel">
          <p className="eyebrow">APPROVED DIRECTION</p>
          <h2>Create asset manifest</h2>
          <p className="muted">
            The manifest includes character model sheets, expression sheets, reusable backgrounds,
            and a keyframe for every approved shot.
          </p>
          {approvedDirections.length === 0 && <p className="warning">Approve a shot plan on the Direction page first.</p>}
          {approvedDirections.map((job) => (
            <article className="job succeeded" key={job.id}>
              <h3>{job.result?.title}</h3>
              <button type="button" onClick={() => action(`/api/v1/direction-jobs/${job.id}/visual-assets/plan`, "Visual asset plan created. Foundational references were queued automatically.")}>Plan visual assets</button>
            </article>
          ))}
        </div>
        <aside>
          <p className="eyebrow">PRODUCTION RULE</p>
          <h2>Reference first</h2>
          <p className="muted">
            Approve the exact character model and location background before queueing dependent
            expression sheets or shot keyframes. The API enforces this even if the UI is bypassed.
          </p>
        </aside>
      </section>

      {grouped.map(([type, items]) => (
        <section className="asset-section" key={type}>
          <div className="asset-heading">
            <p className="eyebrow">{type.replaceAll("_", " ")}</p>
            <strong>{items.length} assets</strong>
          </div>
          <div className="asset-grid">
            {items.map((asset) => (
              <article className={`asset-card ${asset.status}`} key={asset.id}>
                {asset.images[0] && <img src={asset.images[0].url} alt={asset.spec.name} />}
                <div className="asset-body">
                  <div className="job-head"><span className="status">{asset.status}</span><small>{asset.review_status} · attempt {asset.attempts}</small></div>
                  <h3>{asset.spec.name}</h3>
                  {asset.spec.scene_number && <small>Scene {asset.spec.scene_number} · Shot {asset.spec.shot_number}</small>}
                  {asset.spec.dependency_keys.length > 0 && <p className="muted">Requires: {asset.spec.dependency_keys.join(", ")}</p>}
                  {asset.error && <p className="error">{asset.error}</p>}
                  {(asset.status === "planned" || asset.status === "blocked") && <button type="button" onClick={() => action(`/api/v1/visual-assets/${asset.id}/queue`, "Visual asset queued.")}>Queue asset</button>}
                  {asset.status === "failed" && <button className="secondary" type="button" onClick={() => action(`/api/v1/visual-assets/${asset.id}/retry`, "Visual asset queued again.")}>Retry</button>}
                  {asset.status === "succeeded" && <div className="actions"><button type="button" onClick={() => action(`/api/v1/visual-assets/${asset.id}/review`, "Visual asset approved.", { decision: "approved", notes: "Approved as a production reference." })}>Approve</button><button className="secondary" type="button" onClick={() => action(`/api/v1/visual-assets/${asset.id}/review`, "Visual asset returned for regeneration.", { decision: "changes_requested", notes: "Regenerate while preserving permanent identity." })}>Request changes</button></div>}
                </div>
              </article>
            ))}
          </div>
        </section>
      ))}
    </main>
  );
}
