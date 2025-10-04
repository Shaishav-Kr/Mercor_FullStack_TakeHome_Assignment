// frontend/components/SelectedPanel.js
import React from "react";

export default function SelectedPanel({ selected = [] }) {
  return (
    <div className="selected-panel">
      <h3>Selected ( {selected.length} / 5 )</h3>
      {selected.length === 0 && <div className="small">No candidates selected yet — try Auto-Select or pick manually.</div>}
      <ul>
        {selected.map(s => (
          <li key={s.id} style={{marginBottom: "8px"}}>
            <strong>{s.name}</strong> — <span className="small">{s.location}</span>
            <div className="small">Score: {s.score} | Skills: {s.skills.join(", ")}</div>
            <div className="small">Why: {s.reason}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}