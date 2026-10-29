import React from "react";
import { Activity, ShieldAlert, Scissors } from "lucide-react";
import { executeTransformation } from "../services/api";

export default function OutlierVisualizer({
  datasetId,
  outlierSummaries,
  onTransformationApplied,
}) {
  if (!outlierSummaries || outlierSummaries.length === 0) {
    return (
      <div className="card">
        <div className="card-title">
          <Activity size={20} color="#20309A" />
          <span>Numeric Outlier Distribution & Boxplot Visualizer</span>
        </div>
        <p style={{ fontSize: "0.9rem", color: "#475569" }}>
          No numeric columns with sufficient values available for outlier visualization. If your dataset has numbers stored as strings (e.g. <code>annual_salary</code>), convert them to numeric first!
        </p>
      </div>
    );
  }

  const handleCapColumnOutliers = async (colName) => {
    const res = await executeTransformation(datasetId, {
      operation: "cap_outliers",
      columns: [colName],
      parameters: { iqr_multiplier: 1.5 },
      approved_by_user: true,
    });
    if (onTransformationApplied) {
      await onTransformationApplied(res.message);
    }
  };

  const scalePos = (val, minVal, maxVal) => {
    if (maxVal <= minVal) return 50;
    const pct = ((val - minVal) / (maxVal - minVal)) * 100;
    return Math.max(2, Math.min(98, pct));
  };

  return (
    <div className="card">
      <div className="card-title">
        <Activity size={20} color="#20309A" />
        <span>Interactive Boxplot & Dual Outlier Visualizer (1.5× IQR + Modified Z-Score)</span>
      </div>

      <p style={{ fontSize: "0.88rem", color: "#475569", marginBottom: "1.25rem" }}>
        Visualizes the 5-number summary (<strong>Min, Q25, Median, Q75, Max</strong>) in{" "}
        <strong style={{ color: "#20309A" }}>Royal Blue</strong> and highlights extreme outlier points in{" "}
        <strong style={{ color: "#BB232B" }}>Tomato Red</strong>. Unusual values are never deleted automatically.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        {outlierSummaries.map((item) => {
          const q25Left = scalePos(item.q25, item.min_val, item.max_val);
          const q75Left = scalePos(item.q75, item.min_val, item.max_val);
          const medLeft = scalePos(item.median, item.min_val, item.max_val);
          const boxWidth = Math.max(3, q75Left - q25Left);
          const hasOutliers = item.iqr_outlier_count > 0 || item.mod_z_outlier_count > 0;

          return (
            <div
              key={item.column}
              style={{
                border: "1px solid #D8E0F0",
                borderLeft: `4px solid ${hasOutliers ? "#BB232B" : "#20309A"}`,
                borderRadius: "10px",
                padding: "1.15rem 1.25rem",
                background: "#FFFFFF",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                  marginBottom: "0.85rem",
                }}
              >
                <div>
                  <span
                    style={{
                      fontFamily: "monospace",
                      fontSize: "1rem",
                      fontWeight: 800,
                      color: "#20309A",
                      marginRight: "0.75rem",
                    }}
                  >
                    {item.column}
                  </span>
                  <span className={`badge ${hasOutliers ? "badge-modified" : "badge-unchanged"}`}>
                    IQR Outliers: {item.iqr_outlier_count} | Mod Z-Score Outliers: {item.mod_z_outlier_count} ({item.outlier_percentage}%)
                  </span>
                </div>

                {hasOutliers && (
                  <button
                    className="btn-danger"
                    style={{ padding: "0.4rem 0.85rem", fontSize: "0.8rem" }}
                    onClick={() => handleCapColumnOutliers(item.column)}
                  >
                    <Scissors size={13} style={{ marginRight: "4px", verticalAlign: "middle" }} />
                    Approve & Cap Outliers to [{item.lower_fence}, {item.upper_fence}]
                  </button>
                )}
              </div>

              {/* Horizontal Boxplot Track */}
              <div
                style={{
                  position: "relative",
                  height: "42px",
                  background: "#F7F9FC",
                  border: "1px solid #D8E0F0",
                  borderRadius: "8px",
                  margin: "0.75rem 0",
                }}
              >
                {/* Whisker Line */}
                <div
                  style={{
                    position: "absolute",
                    top: "20px",
                    left: "4%",
                    right: "4%",
                    height: "2px",
                    background: "#94A3B8",
                  }}
                />

                {/* IQR Box (Q25 to Q75) */}
                <div
                  style={{
                    position: "absolute",
                    top: "8px",
                    left: `${q25Left}%`,
                    width: `${boxWidth}%`,
                    height: "24px",
                    background: "#EEF1FB",
                    border: "2px solid #20309A",
                    borderRadius: "4px",
                  }}
                  title={`IQR: [${item.q25}, ${item.q75}]`}
                />

                {/* Median Line */}
                <div
                  style={{
                    position: "absolute",
                    top: "6px",
                    left: `${medLeft}%`,
                    width: "3px",
                    height: "28px",
                    background: "#20309A",
                  }}
                  title={`Median: ${item.median}`}
                />

                {/* Sample Outlier Dots in Tomato Red */}
                {item.sample_outliers.map((outVal, idx) => {
                  const dotPos = scalePos(outVal, item.min_val, item.max_val);
                  return (
                    <div
                      key={idx}
                      title={`Outlier value: ${outVal}`}
                      style={{
                        position: "absolute",
                        top: "14px",
                        left: `${dotPos}%`,
                        width: "12px",
                        height: "12px",
                        borderRadius: "50%",
                        background: "#BB232B",
                        border: "2px solid #FFFFFF",
                        boxShadow: "0 0 4px rgba(187,35,43,0.6)",
                        transform: "translateX(-50%)",
                      }}
                    />
                  );
                })}
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  flexWrap: "wrap",
                  fontSize: "0.8rem",
                  color: "#475569",
                  marginTop: "0.4rem",
                }}
              >
                <span><strong>Min:</strong> {item.min_val}</span>
                <span><strong>Lower Fence:</strong> {item.lower_fence}</span>
                <span style={{ color: "#20309A" }}><strong>Q25:</strong> {item.q25}</span>
                <span style={{ color: "#20309A", fontWeight: 700 }}><strong>Median:</strong> {item.median}</span>
                <span style={{ color: "#20309A" }}><strong>Q75:</strong> {item.q75}</span>
                <span><strong>Upper Fence:</strong> {item.upper_fence}</span>
                <span><strong>Max:</strong> {item.max_val}</span>
              </div>

              {item.sample_outliers.length > 0 && (
                <div style={{ marginTop: "0.55rem", fontSize: "0.8rem", color: "#BB232B" }}>
                  <ShieldAlert size={13} style={{ marginRight: "4px", verticalAlign: "text-bottom" }} />
                  <strong>Flagged Extreme Values:</strong> {item.sample_outliers.join(", ")}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}