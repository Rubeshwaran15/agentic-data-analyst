import React, { useState } from "react";
import { Cpu, CheckCircle2, ShieldCheck } from "lucide-react";
import { executeMLPipeline } from "../services/api";

export default function MLPipelineStudio({
  datasetId,
  columns,
  targetColumn,
  onTargetColumnChange,
  onPipelineCompleted,
}) {
  const [trainSize, setTrainSize] = useState(0.8);
  const [imputeStrategy, setImputeStrategy] = useState("median");
  const [scalerMethod, setScalerMethod] = useState("standard");
  const [oneHotEncode, setOneHotEncode] = useState(true);
  const [dropConstants, setDropConstants] = useState(true);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [isBusy, setIsBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleRunPipeline = async () => {
    setIsBusy(true);
    setErrorMsg("");
    try {
      const res = await executeMLPipeline(datasetId, {
        target_column: targetColumn || null,
        train_size: Number(trainSize),
        numeric_impute_strategy: imputeStrategy,
        scaler_method: scalerMethod,
        one_hot_encode_categoricals: oneHotEncode,
        drop_constant_columns: dropConstants,
        approved_by_user: true,
      });
      setPipelineResult(res);
      if (onPipelineCompleted) {
        await onPipelineCompleted(
          `Executed Leak-Free ML Pipeline (Train: ${res.train_rows} rows, Test: ${res.test_rows} rows).`
        );
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <div className="card">
      <div className="card-title">
        <Cpu size={20} color="#20309A" />
        <span>Leak-Free Machine Learning Pipeline Studio</span>
      </div>

      <p style={{ fontSize: "0.88rem", color: "#475569", marginBottom: "1.2rem" }}>
        Automatically preserves identifier columns, splits your dataset into{" "}
        <strong>Training</strong> and <strong>Test</strong> sets <em>before</em> fitting
        imputers or scalers, fits strictly on Training data to prevent data leakage, and
        tags records with an <code>ml_split</code> column.
      </p>

      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
          gap: "1.1rem",
          marginBottom: "1.25rem",
        }}
      >
        <div>
          <label style={{ display: "block", fontSize: "0.83rem", fontWeight: 700, color: "#20309A", marginBottom: "0.35rem" }}>
            1. Target Column (Optional — checks Imbalance & Leakage)
          </label>
          <select
            className="search-input"
            value={targetColumn}
            onChange={(e) => onTargetColumnChange(e.target.value)}
          >
            <option value="">-- Unsupervised / No Target --</option>
            {columns.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.83rem", fontWeight: 700, color: "#20309A", marginBottom: "0.35rem" }}>
            2. Train / Test Split Ratio ({Math.round(trainSize * 100)}% Train / {Math.round((1 - trainSize) * 100)}% Test)
          </label>
          <select
            className="search-input"
            value={trainSize}
            onChange={(e) => setTrainSize(parseFloat(e.target.value))}
          >
            <option value={0.8}>80% Train / 20% Test (Standard)</option>
            <option value={0.75}>75% Train / 25% Test</option>
            <option value={0.7}>70% Train / 30% Test</option>
            <option value={0.9}>90% Train / 10% Test</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.83rem", fontWeight: 700, color: "#20309A", marginBottom: "0.35rem" }}>
            3. Numeric Missing Imputer (Fit on Train Only)
          </label>
          <select
            className="search-input"
            value={imputeStrategy}
            onChange={(e) => setImputeStrategy(e.target.value)}
          >
            <option value="median">Median Imputer (Outlier-Resistant)</option>
            <option value="mean">Mean Imputer</option>
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "0.83rem", fontWeight: 700, color: "#20309A", marginBottom: "0.35rem" }}>
            4. Feature Scaling (Fit on Train Only)
          </label>
          <select
            className="search-input"
            value={scalerMethod}
            onChange={(e) => setScalerMethod(e.target.value)}
          >
            <option value="standard">StandardScaler (Zero Mean, Unit Variance)</option>
            <option value="robust">RobustScaler (IQR-Based)</option>
            <option value="minmax">MinMaxScaler ([0, 1] Range)</option>
            <option value="none">No Feature Scaling</option>
          </select>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap", marginBottom: "1.25rem", fontSize: "0.86rem" }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.45rem", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={oneHotEncode}
            onChange={(e) => setOneHotEncode(e.target.checked)}
          />
          <span>One-Hot Encode Low-Cardinality Categoricals</span>
        </label>

        <label style={{ display: "flex", alignItems: "center", gap: "0.45rem", cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={dropConstants}
            onChange={(e) => setDropConstants(e.target.checked)}
          />
          <span>Drop Constant (Zero-Variance) Columns</span>
        </label>
      </div>

      <button className="btn-primary" disabled={isBusy} onClick={handleRunPipeline}>
        <CheckCircle2 size={16} style={{ marginRight: "6px", verticalAlign: "middle" }} />
        {isBusy ? "Running Leak-Free ML Pipeline..." : "Approve & Execute Leak-Free ML Pipeline"}
      </button>

      {pipelineResult && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1.1rem",
            borderRadius: "10px",
            background: "#EEF1FB",
            borderLeft: "4px solid #20309A",
          }}
        >
          <h4 style={{ color: "#20309A", marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <ShieldCheck size={18} />
            <span>ML Pipeline Validated & Committed (Snapshot v{pipelineResult.snapshot_version})</span>
          </h4>
          <p style={{ fontSize: "0.86rem", marginBottom: "0.5rem" }}>
            <strong>Train Split:</strong> {pipelineResult.train_rows} rows |{" "}
            <strong>Test Split:</strong> {pipelineResult.test_rows} rows |{" "}
            <strong>Columns:</strong> {pipelineResult.features_before} → {pipelineResult.features_after} |{" "}
            <strong>Preserved IDs:</strong> {pipelineResult.preserved_identifiers.join(", ") || "None"}
          </p>
          <ul style={{ paddingLeft: "1.2rem", fontSize: "0.83rem", color: "#0F172A" }}>
            {pipelineResult.steps_applied.map((s, idx) => (
              <li key={idx}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}