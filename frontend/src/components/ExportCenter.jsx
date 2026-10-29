import React from "react";
import { Download, FileText, FileSpreadsheet, FileCode } from "lucide-react";
import {
  getCleanedDatasetDownloadUrl,
  getAuditReportDownloadUrl,
} from "../services/api";

export default function ExportCenter({
  datasetId,
  filename,
  comparisonData,
  historyData,
}) {
  if (!datasetId) return null;

  const datasetFormats = [
    {
      fmt: "csv",
      title: "Cleaned CSV Dataset (.csv)",
      desc: "Universal comma-separated format compatible with Pandas, SQL, and Excel.",
    },
    {
      fmt: "xlsx",
      title: "Cleaned Excel Workbook (.xlsx)",
      desc: "Formatted Microsoft Excel spreadsheet for business reporting.",
    },
    {
      fmt: "json",
      title: "Cleaned JSON Records (.json)",
      desc: "ISO-formatted JSON array of records ready for web APIs and document stores.",
    },
    {
      fmt: "parquet",
      title: "Apache Parquet Columnar (.parquet)",
      desc: "High-speed, type-preserving compressed binary format for ML & Data Engineering.",
    },
  ];

  const reportFormats = [
    {
      fmt: "html",
      title: "Executive Visual Audit Report (.html)",
      desc: "Styled Royal Blue & Tomato Red standalone report (Open in browser or Print to PDF).",
      badge: "Recommended",
    },
    {
      fmt: "md",
      title: "Technical Markdown Audit Report (.md)",
      desc: "Clean Markdown tables of before/after stats, header mappings, and audit steps.",
      badge: "GitHub Ready",
    },
    {
      fmt: "json",
      title: "Machine-Readable Audit Log (.json)",
      desc: "Complete JSON lineage bundle with schema validation checks and parameters.",
      badge: "JSON Schema",
    },
  ];

  return (
    <div>
      {/* Cleaned Dataset Export Card */}
      <div className="card">
        <div className="card-title">
          <FileSpreadsheet size={20} color="#20309A" />
          <span>
            Export Validated & Cleaned Dataset (Snapshot v
            {historyData?.current_version ?? 0})
          </span>
        </div>

        <p style={{ fontSize: "0.88rem", color: "#475569", marginBottom: "1.15rem" }}>
          Current dataset state has{" "}
          <strong style={{ color: "#20309A" }}>
            {comparisonData?.rows_current?.toLocaleString()} rows ×{" "}
            {comparisonData?.cols_current} columns
          </strong>{" "}
          with{" "}
          <strong style={{ color: "#20309A" }}>
            {comparisonData?.missing_current} missing cells
          </strong>
          . Your original uploaded file (<code>{filename}</code>) remains untouched.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: "1rem",
          }}
        >
          {datasetFormats.map((item) => (
            <div
              key={item.fmt}
              style={{
                border: "1px solid #D8E0F0",
                borderTop: "4px solid #20309A",
                borderRadius: "10px",
                padding: "1.1rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                background: "#FFFFFF",
              }}
            >
              <div>
                <h4 style={{ color: "#20309A", fontSize: "0.95rem", marginBottom: "0.35rem" }}>
                  {item.title}
                </h4>
                <p style={{ fontSize: "0.82rem", color: "#475569", marginBottom: "1rem" }}>
                  {item.desc}
                </p>
              </div>

              <a
                href={getCleanedDatasetDownloadUrl(datasetId, item.fmt)}
                download
                className="btn-primary"
                style={{
                  textDecoration: "none",
                  textAlign: "center",
                  display: "inline-flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <Download size={15} />
                <span>Download .{item.fmt.toUpperCase()}</span>
              </a>
            </div>
          ))}
        </div>
      </div>

      {/* Audit & Quality Reports Card */}
      <div className="card">
        <div className="card-title">
          <FileText size={20} color="#BB232B" />
          <span>Download Data-Quality & Preprocessing Audit Reports</span>
        </div>

        <p style={{ fontSize: "0.88rem", color: "#475569", marginBottom: "1.15rem" }}>
          Includes executive Before vs. After metrics, automatic column-name mapping,
          remaining quality anomalies, and the full immutable transformation log.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "1rem",
          }}
        >
          {reportFormats.map((rep) => (
            <div
              key={rep.fmt}
              style={{
                border: "1px solid #D8E0F0",
                borderTop: "4px solid #BB232B",
                borderRadius: "10px",
                padding: "1.1rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                background: "#FFFFFF",
              }}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.4rem" }}>
                  <h4 style={{ color: "#0F172A", fontSize: "0.95rem" }}>{rep.title}</h4>
                  <span className="badge badge-modified">{rep.badge}</span>
                </div>
                <p style={{ fontSize: "0.82rem", color: "#475569", marginBottom: "1rem" }}>
                  {rep.desc}
                </p>
              </div>

              <a
                href={getAuditReportDownloadUrl(datasetId, rep.fmt)}
                download
                className="btn-danger"
                style={{
                  textDecoration: "none",
                  textAlign: "center",
                  display: "inline-flex",
                  justifyContent: "center",
                  alignItems: "center",
                  gap: "0.4rem",
                }}
              >
                <FileCode size={15} />
                <span>Download Audit Report (.{rep.fmt.toUpperCase()})</span>
              </a>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}