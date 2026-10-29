import React, { useState } from "react";
import { Bot, AlertCircle, Check, X, Eye, Sparkles } from "lucide-react";
import { previewTransformation, executeTransformation } from "../services/api";

export default function AIRecommendations({
  datasetId,
  columns,
  targetColumn,
  userGoal,
  onGoalOrTargetUpdate,
  recommendations,
  onTransformationApplied,
}) {
  const [rejectedIndices, setRejectedIndices] = useState([]);
  const [previewMap, setPreviewMap] = useState({});
  const [busyIdx, setBusyIdx] = useState(null);
  const [isReplanning, setIsReplanning] = useState(false);
  const [actionError, setActionError] = useState("");

  if (!recommendations) return null;

  const isAIGenerated = recommendations.generated_by === "ollama_qwen2.5:1.5b";

  const handleTriggerReplan = async (e) => {
    e.preventDefault();
    setIsReplanning(true);
    setActionError("");
    try {
      await onGoalOrTargetUpdate(targetColumn, userGoal);
      setRejectedIndices([]);
      setPreviewMap({});
    } catch (err) {
      setActionError(err.message);
    } finally {
      setIsReplanning(false);
    }
  };

  const handlePreview = async (rec, idx) => {
    setBusyIdx(idx);
    setActionError("");
    try {
      const effect = await previewTransformation(datasetId, {
        operation: rec.operation,
        columns: rec.columns,
        parameters: rec.parameters || {},
        approved_by_user: false,
      });
      setPreviewMap((prev) => ({ ...prev, [idx]: effect }));
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyIdx(null);
    }
  };

  const handleApproveAndExecute = async (rec, idx) => {
    setBusyIdx(idx);
    setActionError("");
    try {
      const result = await executeTransformation(datasetId, {
        operation: rec.operation,
        columns: rec.columns,
        parameters: rec.parameters || {},
        approved_by_user: true,
      });
      if (onTransformationApplied) {
        await onTransformationApplied(result.message);
      }
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusyIdx(null);
    }
  };

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "0.75rem",
          marginBottom: "1rem",
        }}
      >
        <div className="card-title" style={{ marginBottom: 0 }}>
          <Bot size={22} color="#20309A" />
          <span>AI Planning Agent (Local Qwen2.5 1.5B via Ollama)</span>
        </div>
        <span
          className="badge"
          style={{
            background: isAIGenerated ? "#EEF1FB" : "#FDECEE",
            color: isAIGenerated ? "#20309A" : "#BB232B",
          }}
        >
          {isAIGenerated ? "Ollama Qwen2.5 1.5B Active" : "Deterministic Fallback Plan"}
        </span>
      </div>

      {/* Goal & Target Selector Form */}
      <form
        onSubmit={handleTriggerReplan}
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.75rem",
          background: "#F7F9FC",
          padding: "0.9rem",
          borderRadius: "10px",
          border: "1px solid #D8E0F0",
          marginBottom: "1.15rem",
          alignItems: "flex-end",
        }}
      >
        <div style={{ flex: "2", minWidth: "240px" }}>
          <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#20309A", marginBottom: "0.25rem" }}>
            Preprocessing Goal for Qwen2.5 1.5B
          </label>
          <input
            type="text"
            className="search-input"
            style={{ maxWidth: "100%" }}
            placeholder="e.g., Prepare dataset for customer churn classification or salary regression..."
            value={userGoal}
            onChange={(e) => onGoalOrTargetUpdate(targetColumn, e.target.value, false)}
          />
        </div>

        <div style={{ flex: "1", minWidth: "180px" }}>
          <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 700, color: "#20309A", marginBottom: "0.25rem" }}>
            ML Target Column (Optional)
          </label>
          <select
            className="search-input"
            value={targetColumn}
            onChange={(e) => onGoalOrTargetUpdate(e.target.value, userGoal, true)}
          >
            <option value="">-- None --</option>
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <button type="submit" className="btn-primary" disabled={isReplanning}>
          <Sparkles size={14} style={{ marginRight: "5px", verticalAlign: "middle" }} />
          {isReplanning ? "Asking Qwen2.5..." : "Update AI Plan"}
        </button>
      </form>

      {actionError && <div className="error-banner">{actionError}</div>}

      <p style={{ fontSize: "0.92rem", color: "#0F172A", fontWeight: 600, marginBottom: "1.1rem" }}>
        {recommendations.summary}
      </p>

      {recommendations.warnings?.length > 0 && (
        <div
          style={{
            background: "#FDECEE",
            borderLeft: "4px solid #BB232B",
            padding: "0.85rem 1rem",
            borderRadius: "8px",
            marginBottom: "1.25rem",
            fontSize: "0.85rem",
            color: "#941920",
          }}
        >
          <div style={{ fontWeight: 700, display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.25rem" }}>
            <AlertCircle size={16} />
            <span>Safety & Quality Warnings:</span>
          </div>
          <ul style={{ paddingLeft: "1.2rem" }}>
            {recommendations.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {recommendations.recommendations.map((rec, idx) => {
          if (rejectedIndices.includes(idx)) return null;
          const effect = previewMap[idx];

          return (
            <div
              key={idx}
              style={{
                background: "#FFFFFF",
                border: "1px solid #D8E0F0",
                borderLeft: `4px solid ${rec.risk === "high" ? "#BB232B" : "#20309A"}`,
                borderRadius: "10px",
                padding: "1.1rem 1.25rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  flexWrap: "wrap",
                  gap: "1rem",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.55rem", marginBottom: "0.4rem" }}>
                    <span
                      style={{
                        fontFamily: "monospace",
                        background: "#EEF1FB",
                        color: "#20309A",
                        padding: "3px 9px",
                        borderRadius: "6px",
                        fontSize: "0.82rem",
                        fontWeight: 700,
                      }}
                    >
                      {rec.operation}
                    </span>
                    <span
                      className="badge"
                      style={{
                        background: rec.risk === "high" ? "#FDECEE" : "#EEF1FB",
                        color: rec.risk === "high" ? "#BB232B" : "#20309A",
                      }}
                    >
                      Risk: {rec.risk.toUpperCase()}
                    </span>
                  </div>

                  {rec.columns?.length > 0 && (
                    <div style={{ fontSize: "0.82rem", color: "#475569", marginBottom: "0.35rem" }}>
                      Target Columns:{" "}
                      <strong style={{ color: "#20309A", fontFamily: "monospace" }}>
                        {rec.columns.join(", ")}
                      </strong>
                    </div>
                  )}

                  <p style={{ fontSize: "0.88rem", color: "#0F172A" }}>{rec.reason}</p>
                </div>

                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                  <button
                    className="btn-outline"
                    disabled={busyIdx === idx}
                    onClick={() => handlePreview(rec, idx)}
                  >
                    <Eye size={14} style={{ marginRight: "4px", verticalAlign: "middle" }} />
                    Preview Effect
                  </button>
                  <button
                    className="btn-primary"
                    disabled={busyIdx === idx}
                    onClick={() => handleApproveAndExecute(rec, idx)}
                  >
                    <Check size={14} style={{ marginRight: "4px", verticalAlign: "middle" }} />
                    {busyIdx === idx ? "Running..." : "Approve & Execute"}
                  </button>
                  <button
                    className="btn-danger"
                    disabled={busyIdx === idx}
                    onClick={() => setRejectedIndices((prev) => [...prev, idx])}
                  >
                    <X size={14} style={{ marginRight: "4px", verticalAlign: "middle" }} />
                    Reject
                  </button>
                </div>
              </div>

              {effect && (
                <div
                  style={{
                    marginTop: "0.9rem",
                    padding: "0.85rem",
                    background: "#F7F9FC",
                    border: "1px solid #D8E0F0",
                    borderRadius: "8px",
                    fontSize: "0.83rem",
                  }}
                >
                  <strong style={{ color: "#20309A" }}>Expected Effect Preview:</strong>{" "}
                  Rows: {effect.rows_before} → <strong>{effect.rows_after}</strong> ({effect.rows_delta >= 0 ? `+${effect.rows_delta}` : effect.rows_delta}) |{" "}
                  Columns: {effect.cols_before} → <strong>{effect.cols_after}</strong> |{" "}
                  Missing Cells: {effect.missing_before} → <strong>{effect.missing_after}</strong> ({effect.missing_delta})
                  <div style={{ marginTop: "0.3rem", color: "#475569" }}>
                    {effect.execution_notes.join(" • ")}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}