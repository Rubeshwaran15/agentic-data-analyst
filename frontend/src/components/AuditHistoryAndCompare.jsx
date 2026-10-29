import React, { useState } from "react";
import {
  History,
  RotateCcw,
  ShieldCheck,
  GitCompare,
  RefreshCw,
} from "lucide-react";
import {
  undoLastTransformation,
  restoreDatasetVersion,
} from "../services/api";

export default function AuditHistoryAndCompare({
  datasetId,
  historyData,
  comparisonData,
  onStateRestored,
}) {
  const [isBusy, setIsBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  if (!historyData || !comparisonData) return null;

  const handleUndo = async () => {
    setIsBusy(true);
    setErrorMsg("");
    try {
      await undoLastTransformation(datasetId);
      if (onStateRestored) {
        await onStateRestored("Undid last preprocessing operation.");
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsBusy(false);
    }
  };

  const handleRestore = async (version) => {
    setIsBusy(true);
    setErrorMsg("");
    try {
      await restoreDatasetVersion(datasetId, version);
      if (onStateRestored) {
        await onStateRestored(`Restored dataset to snapshot version v${version}.`);
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsBusy(false);
    }
  };

  const formatDelta = (val) => {
    if (val === 0) return "0";
    return val > 0 ? `+${val}` : `${val}`;
  };

  return (
    <div>
      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      {/* Before vs After Summary Card */}
      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1rem",
            marginBottom: "1.1rem",
          }}
        >
          <div className="card-title" style={{ marginBottom: 0 }}>
            <GitCompare size={20} color="#20309A" />
            <span>
              Before & After Comparison (Baseline v0 → Current v
              {comparisonData.current_version})
            </span>
          </div>

          <div style={{ display: "flex", gap: "0.6rem" }}>
            <button
              className="btn-outline"
              disabled={!historyData.can_undo || isBusy}
              onClick={handleUndo}
            >
              <RotateCcw size={14} style={{ marginRight: "5px", verticalAlign: "middle" }} />
              Undo Last Step
            </button>
            <button
              className="btn-danger"
              disabled={historyData.current_version === 0 || isBusy}
              onClick={() => handleRestore(0)}
            >
              <RefreshCw size={14} style={{ marginRight: "5px", verticalAlign: "middle" }} />
              Reset to Initial Standardized (v0)
            </button>
          </div>
        </div>

        <div className="kpi-grid" style={{ marginBottom: "1rem" }}>
          <div className="kpi-card">
            <div className="kpi-label">Rows (Before → After)</div>
            <div className="kpi-value">
              {comparisonData.rows_baseline} → {comparisonData.rows_current}
            </div>
            <div className="kpi-sub">
              Delta: <strong>{formatDelta(comparisonData.rows_delta)}</strong> rows
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Columns (Before → After)</div>
            <div className="kpi-value">
              {comparisonData.cols_baseline} → {comparisonData.cols_current}
            </div>
            <div className="kpi-sub">
              Delta: <strong>{formatDelta(comparisonData.cols_delta)}</strong> columns
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Missing Cells</div>
            <div className="kpi-value">
              {comparisonData.missing_baseline} → {comparisonData.missing_current}
            </div>
            <div className="kpi-sub" style={{ color: comparisonData.missing_delta < 0 ? "#20309A" : "#BB232B" }}>
              Delta: <strong>{formatDelta(comparisonData.missing_delta)}</strong> missing cells
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Exact Duplicate Rows</div>
            <div className="kpi-value">
              {comparisonData.duplicates_baseline} → {comparisonData.duplicates_current}
            </div>
            <div className="kpi-sub">
              Delta: <strong>{formatDelta(comparisonData.duplicates_delta)}</strong> duplicates
            </div>
          </div>

          <div className="kpi-card">
            <div className="kpi-label">Quality Risk Score</div>
            <div className="kpi-value">
              {comparisonData.risk_score_baseline} → {comparisonData.risk_score_current}
            </div>
            <div className="kpi-sub">
              Delta: <strong>{formatDelta(comparisonData.risk_score_delta)}</strong> risk points
            </div>
          </div>
        </div>

        {(comparisonData.added_columns.length > 0 ||
          comparisonData.removed_columns.length > 0) && (
          <div
            style={{
              padding: "0.75rem 1rem",
              background: "#EEF1FB",
              borderRadius: "8px",
              fontSize: "0.84rem",
              marginBottom: "1rem",
            }}
          >
            {comparisonData.added_columns.length > 0 && (
              <div>
                <strong style={{ color: "#20309A" }}>Added Columns:</strong>{" "}
                <span style={{ fontFamily: "monospace" }}>
                  {comparisonData.added_columns.join(", ")}
                </span>
              </div>
            )}
            {comparisonData.removed_columns.length > 0 && (
              <div>
                <strong style={{ color: "#BB232B" }}>Dropped Columns:</strong>{" "}
                <span style={{ fontFamily: "monospace" }}>
                  {comparisonData.removed_columns.join(", ")}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Audit History & Snapshot Timeline */}
      <div className="card">
        <div className="card-title">
          <History size={20} color="#20309A" />
          <span>Immutable Audit Trail & Validated Checkpoints</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Version</th>
                <th>Operation</th>
                <th>Target Columns</th>
                <th>Dimensions (Before → After)</th>
                <th>Missing (Before → After)</th>
                <th>Validation Agent</th>
                <th>Execution Notes</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {historyData.entries.map((entry) => {
                const isCurrent = entry.version === historyData.current_version;
                return (
                  <tr key={entry.version}>
                    <td style={{ fontWeight: 700, color: "#20309A" }}>
                      v{entry.version} {isCurrent && <span className="badge badge-modified">Active</span>}
                    </td>
                    <td style={{ fontFamily: "monospace", fontWeight: 700 }}>
                      {entry.operation}
                    </td>
                    <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                      {entry.columns.length > 0 ? entry.columns.join(", ") : "All Columns"}
                    </td>
                    <td>
                      {entry.rows_before}×{entry.cols_before} →{" "}
                      <strong>
                        {entry.rows_after}×{entry.cols_after}
                      </strong>
                    </td>
                    <td>
                      {entry.missing_before} → <strong>{entry.missing_after}</strong>
                    </td>
                    <td>
                      <span className="badge badge-unchanged">
                        <ShieldCheck
                          size={12}
                          style={{ marginRight: "3px", verticalAlign: "text-bottom" }}
                        />
                        {entry.validation_passed ? "Verified" : "Failed"}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.82rem" }}>{entry.notes.join(" • ")}</td>
                    <td>
                      {!isCurrent ? (
                        <button
                          className="btn-outline"
                          style={{ padding: "0.3rem 0.65rem", fontSize: "0.76rem" }}
                          disabled={isBusy}
                          onClick={() => handleRestore(entry.version)}
                        >
                          Restore v{entry.version}
                        </button>
                      ) : (
                        <span style={{ fontSize: "0.78rem", color: "#475569" }}>
                          Current State
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}