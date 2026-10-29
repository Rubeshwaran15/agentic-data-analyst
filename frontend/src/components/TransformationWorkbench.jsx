import React, { useState } from "react";
import { Sliders, Eye, CheckCircle } from "lucide-react";
import { previewTransformation, executeTransformation } from "../services/api";

const OPERATIONS = [
  { value: "impute_numeric_median", label: "Impute Numeric Missing (Median)", needsCols: true },
  { value: "impute_numeric_mean", label: "Impute Numeric Missing (Mean)", needsCols: true },
  { value: "impute_categorical_mode", label: "Impute Categorical Missing (Mode)", needsCols: true },
  { value: "impute_constant", label: "Impute Missing with Constant", needsCols: true },
  { value: "remove_exact_duplicates", label: "Remove Exact Duplicate Rows", needsCols: false },
  { value: "remove_empty_rows", label: "Remove Completely Empty Rows", needsCols: false },
  { value: "normalize_text", label: "Normalize Text (Trim & Case)", needsCols: true },
  { value: "convert_to_numeric", label: "Convert Strings to Numeric", needsCols: true },
  { value: "cap_outliers", label: "Cap Numeric Outliers (1.5x IQR)", needsCols: true },
  { value: "remove_outliers", label: "Remove Numeric Outlier Rows (1.5x IQR)", needsCols: true },
  { value: "one_hot_encode", label: "One-Hot Encode Nominal Categories", needsCols: true },
  { value: "apply_scaler", label: "Scale Numeric Columns (Standard / MinMax / Robust)", needsCols: true },
  { value: "drop_columns", label: "Drop Selected Columns", needsCols: true },
];

export default function TransformationWorkbench({
  datasetId,
  columns,
  onTransformationApplied,
}) {
  const [operation, setOperation] = useState("impute_numeric_median");
  const [selectedCols, setSelectedCols] = useState([]);
  const [scalerMethod, setScalerMethod] = useState("standard");
  const [constantVal, setConstantVal] = useState("Unknown");
  const [useMlSplit, setUseMlSplit] = useState(false);
  const [previewEffect, setPreviewEffect] = useState(null);
  const [isBusy, setIsBusy] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const currentOpMeta = OPERATIONS.find((o) => o.value === operation);

  const toggleColumn = (col) => {
    setSelectedCols((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  };

  const buildParameters = () => {
    if (operation === "apply_scaler") return { method: scalerMethod };
    if (operation === "impute_constant") return { fill_value: constantVal };
    if (operation === "normalize_text") return { trim_whitespace: true, normalize_case: true };
    return {};
  };

  const handlePreview = async () => {
    setIsBusy(true);
    setErrorMsg("");
    try {
      const effect = await previewTransformation(datasetId, {
        operation,
        columns: currentOpMeta?.needsCols ? selectedCols : [],
        parameters: buildParameters(),
        use_ml_train_test_split: useMlSplit,
        approved_by_user: false,
      });
      setPreviewEffect(effect);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsBusy(false);
    }
  };

  const handleExecute = async () => {
    setIsBusy(true);
    setErrorMsg("");
    try {
      const res = await executeTransformation(datasetId, {
        operation,
        columns: currentOpMeta?.needsCols ? selectedCols : [],
        parameters: buildParameters(),
        use_ml_train_test_split: useMlSplit,
        approved_by_user: true,
      });
      setPreviewEffect(null);
      if (onTransformationApplied) {
        await onTransformationApplied(res.message);
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
        <Sliders size={20} color="#20309A" />
        <span>Safe Preprocessing Execution Workbench</span>
      </div>

      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginBottom: "1.25rem" }}>
        <div>
          <label style={{ display: "block", fontWeight: 700, fontSize: "0.85rem", color: "#20309A", marginBottom: "0.4rem" }}>
            1. Select Allowlisted Operation
          </label>
          <select
            className="search-input"
            style={{ maxWidth: "100%" }}
            value={operation}
            onChange={(e) => {
              setOperation(e.target.value);
              setPreviewEffect(null);
            }}
          >
            {OPERATIONS.map((op) => (
              <option key={op.value} value={op.value}>
                {op.label}
              </option>
            ))}
          </select>

          {operation === "apply_scaler" && (
            <div style={{ marginTop: "0.75rem" }}>
              <label style={{ fontSize: "0.82rem", fontWeight: 600 }}>Scaler Type: </label>
              <select
                className="search-input"
                style={{ width: "auto", marginLeft: "0.5rem" }}
                value={scalerMethod}
                onChange={(e) => setScalerMethod(e.target.value)}
              >
                <option value="standard">StandardScaler (Z-score)</option>
                <option value="minmax">MinMaxScaler (0 to 1)</option>
                <option value="robust">RobustScaler (IQR-based)</option>
              </select>
            </div>
          )}

          {operation === "impute_constant" && (
            <div style={{ marginTop: "0.75rem" }}>
              <label style={{ fontSize: "0.82rem", fontWeight: 600 }}>Constant Fill Value: </label>
              <input
                type="text"
                className="search-input"
                style={{ width: "200px", marginLeft: "0.5rem" }}
                value={constantVal}
                onChange={(e) => setConstantVal(e.target.value)}
              />
            </div>
          )}

          <div style={{ marginTop: "0.85rem" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.84rem", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={useMlSplit}
                onChange={(e) => setUseMlSplit(e.target.checked)}
              />
              <span>Fit transformation on 80% Training Split only (ML leakage prevention)</span>
            </label>
          </div>
        </div>

        {currentOpMeta?.needsCols && (
          <div>
            <label style={{ display: "block", fontWeight: 700, fontSize: "0.85rem", color: "#20309A", marginBottom: "0.4rem" }}>
              2. Select Target Columns ({selectedCols.length} selected)
            </label>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: "0.45rem",
                maxHeight: "135px",
                overflowY: "auto",
                padding: "0.65rem",
                border: "1px solid #D8E0F0",
                borderRadius: "8px",
              }}
            >
              {columns.map((col) => {
                const active = selectedCols.includes(col);
                return (
                  <button
                    key={col}
                    type="button"
                    onClick={() => toggleColumn(col)}
                    style={{
                      padding: "0.3rem 0.65rem",
                      borderRadius: "6px",
                      fontSize: "0.78rem",
                      fontFamily: "monospace",
                      fontWeight: 600,
                      cursor: "pointer",
                      border: active ? "1px solid #20309A" : "1px solid #D8E0F0",
                      background: active ? "#20309A" : "#FFFFFF",
                      color: active ? "#FFFFFF" : "#0F172A",
                    }}
                  >
                    {col}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "0.75rem" }}>
        <button className="btn-outline" disabled={isBusy} onClick={handlePreview}>
          <Eye size={15} style={{ marginRight: "5px", verticalAlign: "middle" }} />
          Preview Expected Effect
        </button>
        <button className="btn-primary" disabled={isBusy} onClick={handleExecute}>
          <CheckCircle size={15} style={{ marginRight: "5px", verticalAlign: "middle" }} />
          Approve & Execute Operation
        </button>
      </div>

      {previewEffect && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1rem",
            borderRadius: "10px",
            background: "#EEF1FB",
            border: "1px solid #20309A",
          }}
        >
          <h4 style={{ color: "#20309A", marginBottom: "0.5rem" }}>
            Dry-Run Before & After Comparison
          </h4>
          <p style={{ fontSize: "0.86rem", marginBottom: "0.5rem" }}>
            <strong>Rows:</strong> {previewEffect.rows_before} → {previewEffect.rows_after} ({previewEffect.rows_delta}) |{" "}
            <strong>Columns:</strong> {previewEffect.cols_before} → {previewEffect.cols_after} ({previewEffect.cols_delta}) |{" "}
            <strong>Missing Values:</strong> {previewEffect.missing_before} → {previewEffect.missing_after} ({previewEffect.missing_delta})
          </p>
          <p style={{ fontSize: "0.84rem", color: "#BB232B", fontWeight: 600 }}>
            {previewEffect.execution_notes.join(" • ")}
          </p>
        </div>
      )}
    </div>
  );
}