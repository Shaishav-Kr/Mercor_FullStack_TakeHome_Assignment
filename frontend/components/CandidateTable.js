// frontend/components/CandidateTable.js
import React from "react";

export default function CandidateTable({ candidates = [], onSelect }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Location</th>
          <th>Skills</th>
          <th>Exp (yrs)</th>
          <th>Salary</th>
          <th>Score</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {candidates.map(c => (
          <tr key={c.id}>
            <td>
              <div><strong>{c.name}</strong></div>
              <div className="small">{c.email}</div>
            </td>
            <td>{c.location}</td>
            <td>{(c.skills || []).slice(0,4).join(", ")}</td>
            <td>{c.experience_years}</td>
            <td>{c.salary_expectation ? `$${c.salary_expectation}` : "-"}</td>
            <td><strong>{c.score}</strong></td>
            <td><button className="button ghost" onClick={() => onSelect(c.id)}>Select</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}