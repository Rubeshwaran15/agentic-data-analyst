import React, { useState } from "react";
import { BarChart3, Search } from "lucide-react";

export default function ProfileExplorer({ profile }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  if (!profile) return null;

  const filteredColumns = profile.column_profiles.filter((col) => {
    const matchesSearch =
      col.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      col.original_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === "all" || col.semantic_type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
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
          <BarChart3 size={20} />
          <span>Column Profiles & Statistical Summary ({filteredColumns.length})</span>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <Search
              size={16}
              style={{ position: "absolute", left: "10px", top: "10px", color: "#6B7D47" }}
            />
            <input
              type="text"
              className="search-input"
              style={{ paddingLeft: "2rem" }}
              placeholder="Search column name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <select
            className="search-input"
            style={{ width: "auto" }}
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">All Semantic Types</option>
            <option value="numeric">Numeric</option>
            <option value="categorical">Categorical</option>
            <option value="boolean">Boolean</option>
            <option value="datetime">Datetime</option>
            <option value="identifier">Identifier</option>
            <option value="text">Text</option>
          </select>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Standardized Column</th>
              <th>Semantic Class</th>
              <th>Pandas Dtype</th>
              <th>Missing Values</th>
              <th>Unique Values</th>
              <th>Numeric Statistics / Frequent Categories</th>
            </tr>
          </thead>
          <tbody>
            {filteredColumns.map((col) => (
              <tr key={col.name}>
                <td>
                  <div style={{ fontWeight: 700, fontFamily: "monospace", color: "#2F3E15" }}>
                    {col.name}
                  </div>
                  {col.original_name !== col.name && (
                    <div style={{ fontSize: "0.75rem", color: "#535B44" }}>
                      Orig: {col.original_name}
                    </div>
                  )}
                </td>
                <td>
                  <span className="badge badge-type">{col.semantic_type}</span>
                </td>
                <td style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>
                  {col.pandas_dtype}
                </td>
                <td>
                  <span
                    style={{
                      color: col.null_count > 0 ? "#B45309" : "#2E6F40",
                      fontWeight: 600,
                    }}
                  >
                    {col.null_count.toLocaleString()} ({col.null_percentage}%)
                  </span>
                </td>
                <td>
                  {col.unique_count.toLocaleString()} ({col.unique_percentage}%)
                </td>
                <td>
                  {col.numeric_stats ? (
                    <div style={{ fontSize: "0.8rem", lineHeight: 1.45 }}>
                      <span>
                        <strong>Mean:</strong> {col.numeric_stats.mean ?? "N/A"} |{" "}
                        <strong>Std:</strong> {col.numeric_stats.std ?? "N/A"} |{" "}
                        <strong>Median:</strong> {col.numeric_stats.median ?? "N/A"}
                      </span>
                      <br />
                      <span>
                        <strong>Min:</strong> {col.numeric_stats.min ?? "N/A"} |{" "}
                        <strong>IQR:</strong> [{col.numeric_stats.q25 ?? "N/A"},{" "}
                        {col.numeric_stats.q75 ?? "N/A"}] | <strong>Max:</strong>{" "}
                        {col.numeric_stats.max ?? "N/A"} | <strong>Skew:</strong>{" "}
                        {col.numeric_stats.skewness ?? "N/A"}
                      </span>
                    </div>
                  ) : (
                    <div style={{ fontSize: "0.8rem" }}>
                      {col.top_values.length > 0 ? (
                        col.top_values.map((tv, idx) => (
                          <span
                            key={idx}
                            style={{
                              display: "inline-block",
                              background: "#F2ECE1",
                              padding: "2px 7px",
                              borderRadius: "5px",
                              marginRight: "5px",
                              marginBottom: "4px",
                            }}
                          >
                            {tv.value}: <strong>{tv.count}</strong> ({tv.percentage}%)
                          </span>
                        ))
                      ) : (
                        <em>No non-null values</em>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}