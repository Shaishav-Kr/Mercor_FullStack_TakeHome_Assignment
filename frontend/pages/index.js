// frontend/pages/index.js
import React, { useEffect, useState } from "react";
import CandidateTable from "../components/CandidateTable";
import SelectedPanel from "../components/SelectedPanel";

export default function Home() {
  const [candidates, setCandidates] = useState([]);
  const [selected, setSelected] = useState([]);
  const [query, setQuery] = useState("");
  const [maxSalary, setMaxSalary] = useState("");
  const [minExp, setMinExp] = useState("");

  const API = "http://localhost:8000/api";

  async function fetchCandidates() {
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (minExp) params.set("min_experience", minExp);
    if (maxSalary) params.set("max_salary", maxSalary);
    const res = await fetch(`${API}/candidates?${params.toString()}`);
    const data = await res.json();
    setCandidates(data.candidates || []);
  }

  async function fetchSelected() {
    const res = await fetch(`${API}/selected`);
    const data = await res.json();
    setSelected(data.selected || []);
  }

  useEffect(() => { fetchCandidates(); fetchSelected(); }, []);

  async function handleSelect(id) {
    await fetch(`${API}/select/${id}`, { method: "POST" });
    await fetchCandidates(); await fetchSelected();
  }

  async function handleUpload(ev) {
    const file = ev.target.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append("file", file);
    const res = await fetch(`${API}/upload`, { method: "POST", body: fd });
    const data = await res.json();
    alert(`Uploaded ${data.count} candidates; re-seeded DB.`);
    await fetchCandidates(); await fetchSelected();
  }

async function handleAutoSelect() {
  const res = await fetch(`${API}/auto_select`, { method: "POST" });
  const data = await res.json();

  if (data.status === "ok" && Array.isArray(data.selected)) {
    // Create a string with the 5 candidates
    const message = data.selected
      .map((c, i) => `${i + 1}. ${c.name} (Score: ${c.score.toFixed(2)})`)
      .join("\n");

    alert(`Auto-selected team:\n\n${message}`);
  } else {
    alert("Auto-select failed. Try again.");
  }

  await fetchCandidates();
  await fetchSelected();
}

  return (
    <div className="container">
      <div className="header">
        <div>
          <h1>Mercor — Hiring Dashboard (Takehome)</h1>
          <div className="small">Upload candidate JSON, filter, auto-select 5 hires, inspect reasons.</div>
        </div>
        <div>
          <input type="file" accept=".json" onChange={handleUpload} />
        </div>
      </div>

      <div className="controls">
        <input placeholder="search name/skills..." value={query} onChange={e=>setQuery(e.target.value)} />
        <input placeholder="min experience (yrs)" value={minExp} onChange={e=>setMinExp(e.target.value)} />
        <input placeholder="max salary (USD)" value={maxSalary} onChange={e=>setMaxSalary(e.target.value)} />
        <button className="button primary" onClick={fetchCandidates}>Apply</button>
        <button className="button ghost" onClick={()=>{ setQuery(""); setMinExp(""); setMaxSalary(""); fetchCandidates(); }}>Clear</button>
        <button className="button primary" onClick={handleAutoSelect}>Auto-select top 5 (diverse)</button>
      </div>

      <CandidateTable candidates={candidates} onSelect={handleSelect} />

      <SelectedPanel selected={selected} />
    </div>
  );
}