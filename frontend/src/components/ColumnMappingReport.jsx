import React from "react";
import { ArrowRightLeft } from "lucide-react";

export default function ColumnMappingReport({ report }) {
  if (!report) return null;

  return (
    <div className="card">
      <div className="card-title">
        <ArrowRightLeft size={20} />
        <span>Automatic Column-Name Standardization Report</span>
      </div>

      <p style={{ fontSize: "0.88rem", color: "#535B44", marginBottom: "1rem" }}>
        Standardized <strong>{report.modified_count}</strong> of{" "}
        <strong>{report.total_columns}</strong> columns (Duplicates resolved:{" "}
        <strong>{report.duplicate_names_resolved}</strong>, Unnamed filled:{" "}
        <strong>{report.empty_names_filled}</strong>). The original dataset file is
        preserved unchanged.
      </p>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Original Column Name</th>
              <th>Standardized Column Name</th>
              <th>Status</th>
              <th>Standardization Actions Applied</th>
            </tr>
          </thead>
          <tbody>
            {report.mappings.map((item) => (
              <tr key={item.index}>
                <td>{item.index + 1}</td>
                <td style={{ fontFamily: "monospace" }}>
                  {item.original_name || <em>(empty)</em>}
                </td>
                <td style={{ fontFamily: "monospace", fontWeight: 700, color: "#2F3E15" }}>
                  {item.standardized_name}
                </td>
                <td>
                  <span
                    className={`badge ${
                      item.was_modified ? "badge-modified" : "badge-unchanged"
                    }`}
                  >
                    {item.was_modified ? "Standardized" : "Unchanged"}
                  </span>
                </td>
                <td>
                  {item.modification_notes.length > 0
                    ? item.modification_notes.join(" • ")
                    : "Already matched snake_case standard"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}