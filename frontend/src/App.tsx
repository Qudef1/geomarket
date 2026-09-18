import { FormEvent, useState } from "react";
import { analyzeArea, analyzePoint, searchPlaces } from "./api";
import { MapView } from "./MapView";
import type { Candidate, Location, PointResponse, SearchResult } from "./types";

const HELSINKI = { latitude: 60.1699, longitude: 24.9384 };

export default function App() {
  const [selected, setSelected] = useState<Location>(HELSINKI);
  const [result, setResult] = useState<PointResponse | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [query, setQuery] = useState("");
  const [matches, setMatches] = useState<SearchResult[]>([]);
  const [bounds, setBounds] = useState({ south: 60.14, west: 24.88, north: 60.21, east: 25.02 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runPoint() {
    setBusy(true); setError(null); setCandidates([]);
    try { setResult(await analyzePoint(selected)); } catch (err) { setError(err instanceof Error ? err.message : "Analysis failed"); }
    finally { setBusy(false); }
  }

  async function runArea() {
    setBusy(true); setError(null); setResult(null);
    try { setCandidates(await analyzeArea(bounds)); } catch (err) { setError(err instanceof Error ? err.message : "Area analysis failed"); }
    finally { setBusy(false); }
  }

  async function submitSearch(event: FormEvent) {
    event.preventDefault(); if (query.trim().length < 2) return;
    setError(null);
    try { setMatches(await searchPlaces(query)); } catch (err) { setError(err instanceof Error ? err.message : "Search failed"); }
  }

  const score = result?.result;
  return (
    <main>
      <header><div className="brand"><span className="brand-mark">G</span><div><strong>GeoMarket</strong><small>Decision intelligence</small></div></div><span className="status"><i /> Helsinki · OSM live</span></header>
      <section className="workspace">
        <aside className="panel control-panel">
          <p className="eyebrow">Location analysis</p><h1>Find the signal<br />in the city.</h1>
          <p className="intro">Evidence-based placement for your next coffee shop.</p>
          <form onSubmit={submitSearch} className="search"><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search Kamppi, Helsinki…" aria-label="Search location" /><button>→</button></form>
          {matches.length > 0 && <div className="matches">{matches.slice(0, 4).map((match) => <button key={match.display_name} onClick={() => { setSelected(match); setMatches([]); }}>{match.display_name}</button>)}</div>}
          <label className="field"><span>Business type</span><select><option>Coffee shop</option></select></label>
          <div className="coordinate"><span>Selected point</span><code>{selected.latitude.toFixed(5)}, {selected.longitude.toFixed(5)}</code></div>
          <p className="hint">Click anywhere on the map to reposition the analysis point.</p>
          <button className="primary" disabled={busy} onClick={runPoint}>{busy ? "Reading the city…" : "Analyze this location"}</button>
          <button className="secondary" disabled={busy} onClick={runArea}>Rank visible area</button>
          {error && <p className="error" role="alert">{error}</p>}
        </aside>
        <MapView selected={selected} result={result} candidates={candidates} onSelect={setSelected} onBounds={setBounds} />
        <aside className="panel result-panel">
          {score ? <>
            <p className="eyebrow">Suitability report</p><div className="score"><strong>{Math.round(score.score * 100)}</strong><span>/100<br /><em>{score.grade}</em></span></div>
            <div className="confidence">Evidence confidence {Math.round(score.confidence * 100)}%</div>
            <h2>Score anatomy</h2>
            {Object.entries(score.components).map(([name, value]) => <div className="metric" key={name}><span>{name.replace("_", " ")}</span><div><i style={{ width: `${value * 100}%` }} /></div><b>{Math.round(value * 100)}</b></div>)}
            <h2>Why this score</h2>
            {[...score.positive_factors.map((text) => ["+", text]), ...score.negative_factors.map((text) => ["−", text])].map(([sign, text], index) => <p className={sign === "+" ? "factor positive" : "factor negative"} key={index}><b>{sign}</b>{text}</p>)}
            {!score.positive_factors.length && !score.negative_factors.length && <p className="empty">No expert rules fired. The score comes from normalized geographic evidence.</p>}
          </> : candidates.length ? <><p className="eyebrow">Area ranking</p><h2>Top visible candidates</h2><div className="ranking">{candidates.map((candidate) => <button key={candidate.rank} onClick={() => setSelected(candidate.location)}><b>#{candidate.rank}</b><span>{candidate.location.latitude.toFixed(4)}, {candidate.location.longitude.toFixed(4)}</span><strong>{Math.round(candidate.result.score * 100)}</strong></button>)}</div></> : <div className="empty-state"><span>◎</span><h2>Your evidence will appear here</h2><p>Choose a point for a detailed score or rank the current map area.</p></div>}
        </aside>
      </section>
    </main>
  );
}

