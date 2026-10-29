import React from "react";
import { Table } from "lucide-react";

export default function DatasetPreview({ preview }) {
  if (!preview) return null;

  return (
    <div className="card">
      <div className="card-title">
        <Table size={20} />
        <span>Dataset Preview (First {preview.preview_rows.length} Rows)</span>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Row</th>
              {preview.columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.preview_rows.map((row, rIdx) => (
              <tr key={rIdx}>
                <td style={{ fontWeight: 600, color: "#6B7D47" }}>{rIdx + 1}</td>
                {preview.columns.map((col) => {
                  const cellVal = row[col];
                  return (
                    <td key={col}>
                      {cellVal === null || cellVal === undefined ? (
                        <span style={{ color: "#B91C1C", fontStyle: "italic" }}>null</span>
                      ) : (
                        String(cellVal)
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}