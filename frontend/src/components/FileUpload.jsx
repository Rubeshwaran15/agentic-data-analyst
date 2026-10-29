import React, { useRef, useState } from "react";
import { UploadCloud, FileSpreadsheet, Download } from "lucide-react";
import { getSampleCsvDownloadUrl } from "../services/api";

export default function FileUpload({ onUploadSuccess, isLoading }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    if (!files || files.length === 0) return;
    onUploadSuccess(files[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
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
          <FileSpreadsheet size={20} color="#20309A" />
          <span>Upload Tabular Dataset</span>
        </div>

        <a
          href={getSampleCsvDownloadUrl()}
          download="sample_messy_test_dataset.csv"
          className="btn-outline"
          style={{ textDecoration: "none", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
        >
          <Download size={15} />
          <span>Download Sample Messy CSV for Testing</span>
        </a>
      </div>

      <div
        className={`upload-zone ${isDragging ? "dragging" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <UploadCloud size={42} color="#20309A" style={{ marginBottom: "0.6rem" }} />
        <p style={{ fontWeight: 700, fontSize: "1rem", color: "#20309A" }}>
          {isLoading
            ? "Parsing, standardizing headers, and running quality & AI agents..."
            : "Drag & drop your dataset here, or click to browse"}
        </p>
        <p style={{ fontSize: "0.84rem", color: "#475569", marginTop: "0.35rem" }}>
          Supported formats: CSV, XLSX, XLS, JSON, Parquet (Max 50 MB)
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json,.parquet"
          style={{ display: "none" }}
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>
    </div>
  );
}