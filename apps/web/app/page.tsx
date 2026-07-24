const stages = [
  "Story",
  "Script",
  "Direction",
  "Visuals",
  "Animation",
  "Voice",
  "Lip Sync",
  "Sound",
  "Quality Control",
  "Render",
];

export default function Home() {
  return (
    <main>
      <section className="hero">
        <p className="eyebrow">PRODUCTION CONTROL PLANE</p>
        <h1>AI Cartoon Studio</h1>
        <p className="lede">
          Build complete original cartoon episodes with permanent characters, reviewable shots,
          replaceable AI providers, and human approval at every critical stage.
        </p>
        <button type="button">Create series</button>
      </section>

      <section className="panel">
        <div>
          <p className="eyebrow">EPISODE PIPELINE</p>
          <h2>One direction from day one</h2>
        </div>
        <div className="grid">
          {stages.map((stage, index) => (
            <article key={stage}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <h3>{stage}</h3>
              <p>Provider-independent, tracked, reviewable, and individually retryable.</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
