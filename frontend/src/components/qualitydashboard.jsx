import React, { useState } from "react";
import { ShieldAlert, AlertTriangle, CheckCircle2, Wrench } from "lucide-react";

export default function QualityDashboard({ quality }) {
  const [filterType, setFilterType] = useState("all");

  if (!quality) return null;

  const filteredIssues = quality.issues.filter((issue) => {
    if (filterType === "confirmed") return issue.is_confirmed;
    if (filterType === "anomalies") return !issue.is_confirmed;
    return true;
  });

  const getSeverityBadge = (severity) => {
    const colors = {
      low: { bg: "#fef3c7", color: "#b45309" },
      medium: { bg: "#fed7aa", color: "#c2410c" },
      high: { bg: "#fee2e2", color: "#b91c1c" },
      critical: { bg: "#7f1d1d", color: "#fee2e2" },
    };
    const style = colors[severity] || colors.medium;
    return (
      <span
        style={{
          background: style.bg,
          color: style.color,
          padding: "2px 8px",
          borderRadius: "999px",
          fontSize: "0.72rem",
          fontWeight: 700,
          textTransform: uppercase,
        }}
      >
        {severity}
      </span>
    );
  };

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.25rem",
        }}
      >
        <div className="card-title" style={{ marginBottom: 0 }}>
          <ShieldAlert size={20} color="#b91c1c" />
          <span>Data-Quality Analysis Engine</span>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <div style={{ fontSize: "0.85rem", fontWeight: 600 }}>
            Risk Score:{" "}
            <span
              style={{
                color: quality.risk_score > 50 ? "#b91c1c" : quality.risk_score > 20 ? "#b45309" : "#2e6f40",
                fontSize: "1.1rem",
              }}
            >
              {quality.risk_score} / 100
            </span>
          </div>

          <select
            className="search-input"
            style={{ width: "auto" }}
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="all">All Issues ({quality.total_issues_found})</option>
            <option value="confirmed">Confirmed Issues ({quality.confirmed_issues_count})</option>
            <option value="anomalies">Potential Anomalies ({quality.potential_anomalies_count})</option>
          </select>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        {filteredIssues.map((issue) => (
          <div
            key={issue.issue_id}
            style={{
              background: "#fffdf7",
              border: "1px solid var(--border-warm)",
              borderLeft: `4px solid ${issue.is_confirmed ? "#b91c1c" : "#b45309"}`,
              borderRadius: "10px",
              padding: "1.1rem",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                <span style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "#6b7d47", fontWeight: 700 }}>
                  {issue.issue_id} • {issue.category.replace("_", " ").toUpperCase()}
                </span>
                {getSeverityBadge(issue.severity)}
              </div>

              <h4 style={{ fontSize: "0.98rem", fontWeight: 700, color: "#2f3e15", marginBottom: "0.35rem" }}>
                {issue.title}
              </h4>

              <p style={{ fontSize: "0.84rem", color: "#535b44", lineHeight: 1.45, marginBottom: "0.75rem" }}>
                {issue.description}
              </p>

              {issue.affected_columns.length > 0 && (
                <div style={{ marginBottom: "0.75rem", fontSize: "0.78rem" }}>
                  <strong>Affected Columns:</strong>{" "}
                  <span style={{ fontFamily: "monospace", color: "#2f3e15" }}>
                    {issue.affected_columns.join(", ")}
                  </span>
                </div>
              )}
            </div>

            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", fontSize: "0.78rem", color: "#6b7d47", fontWeight: 600, marginTop: "0.5rem", borderTop: "1px solid #ede7d9", paddingTop: "0.5rem" }}>
                <Wrench size={14} />
                <span>Suggested: {issue.suggested_operations.join(", ") || "Review"}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}