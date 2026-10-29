from datetime import datetime, timezone
import io
import json
from pathlib import Path
from typing import Any
import pandas as pd
from app.core.exceptions import DatasetError
from app.services.audit_logger import (
    build_before_after_comparison,
    get_audit_history,
)
from app.services.profiler import profile_dataset
from app.services.quality_analyzer import analyze_dataset_quality
from app.services.session_store import session_store


def export_cleaned_dataset_bytes(
    dataset_id: str, export_format: str
) -> tuple[bytes, str, str]:
    """
    Exports the current validated DataFrame snapshot into CSV, XLSX, JSON, or Parquet bytes.
    Returns (file_bytes, media_type, download_filename).
    """
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)

    stem = Path(session.filename).stem
    version_tag = f"v{session.current_version}"
    fmt = export_format.lower().strip(".")

    if fmt == "csv":
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        return csv_bytes, "text/csv", f"{stem}_cleaned_{version_tag}.csv"

    if fmt in ("xlsx", "excel"):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Cleaned_Data")
        return (
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            f"{stem}_cleaned_{version_tag}.xlsx",
        )

    if fmt == "json":
        json_str = df.to_json(orient="records", indent=2, date_format="iso")
        return (
            (json_str or "[]").encode("utf-8"),
            "application/json",
            f"{stem}_cleaned_{version_tag}.json",
        )

    if fmt == "parquet":
        buffer = io.BytesIO()
        df.to_parquet(buffer, engine="pyarrow", index=False)
        return (
            buffer.getvalue(),
            "application/octet-stream",
            f"{stem}_cleaned_{version_tag}.parquet",
        )

    raise DatasetError(
        f"Unsupported export format '{export_format}'. Allowed: csv, xlsx, json, parquet.",
        status_code=400,
    )


def build_comprehensive_audit_payload(dataset_id: str) -> dict[str, Any]:
    """
    Reporting Agent:
    Compiles dataset profile, before-and-after metrics, column standardization report,
    remaining quality issues, and full validated transformation history.
    """
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)

    profile = profile_dataset(df, session)
    quality = analyze_dataset_quality(df)
    quality.dataset_id = dataset_id
    comparison = build_before_after_comparison(dataset_id)
    history = get_audit_history(dataset_id)

    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": dataset_id,
        "original_filename": session.filename,
        "current_snapshot_version": session.current_version,
        "before_after_summary": comparison.model_dump(),
        "column_standardization_report": session.standardization_report.model_dump(),
        "current_quality_analysis": quality.model_dump(),
        "current_dataset_profile": {
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "memory_usage_human": profile.memory_usage_human,
            "total_missing_cells": profile.total_missing_cells,
            "exact_duplicate_rows": profile.exact_duplicate_rows,
            "semantic_type_counts": profile.semantic_type_counts,
        },
        "transformation_audit_trail": [entry.model_dump() for entry in history.entries],
    }


def export_audit_report_bytes(
    dataset_id: str, report_format: str
) -> tuple[bytes, str, str]:
    """
    Generates a downloadable Audit & Data Quality Report in JSON, Markdown, or HTML.
    """
    session = session_store.get_session(dataset_id)
    stem = Path(session.filename).stem
    payload = build_comprehensive_audit_payload(dataset_id)
    fmt = report_format.lower().strip(".")

    if fmt == "json":
        raw = json.dumps(payload, indent=2).encode("utf-8")
        return raw, "application/json", f"{stem}_audit_report.json"

    if fmt in ("md", "markdown"):
        md_text = _render_markdown_report(payload)
        return md_text.encode("utf-8"), "text/markdown", f"{stem}_audit_report.md"

    if fmt == "html":
        html_text = _render_html_report(payload)
        return html_text.encode("utf-8"), "text/html", f"{stem}_audit_report.html"

    raise DatasetError(
        f"Unsupported report format '{report_format}'. Allowed: json, md, html.",
        status_code=400,
    )


def _render_markdown_report(payload: dict[str, Any]) -> str:
    comp = payload["before_after_summary"]
    qual = payload["current_quality_analysis"]
    std = payload["column_standardization_report"]
    lines = [
        f"# Data Quality & Preprocessing Audit Report: {payload['original_filename']}",
        f"**Generated At (UTC):** {payload['report_generated_at']}  ",
        f"**Active Snapshot Version:** v{payload['current_snapshot_version']}",
        "",
        "## 1. Before vs. After Executive Summary",
        "| Metric | Baseline (v0) | Current State | Delta |",
        "| :--- | :---: | :---: | :---: |",
        f"| **Rows** | {comp['rows_baseline']} | {comp['rows_current']} | {comp['rows_delta']} |",
        f"| **Columns** | {comp['cols_baseline']} | {comp['cols_current']} | {comp['cols_delta']} |",
        f"| **Missing Values** | {comp['missing_baseline']} | {comp['missing_current']} | {comp['missing_delta']} |",
        f"| **Exact Duplicates** | {comp['duplicates_baseline']} | {comp['duplicates_current']} | {comp['duplicates_delta']} |",
        f"| **Quality Risk Score** | {comp['risk_score_baseline']}/100 | {comp['risk_score_current']}/100 | {comp['risk_score_delta']} |",
        "",
        "## 2. Column Standardization Mapping",
        f"Modified **{std['modified_count']}** of **{std['total_columns']}** columns.",
        "",
        "| Original Name | Standardized Name | Notes |",
        "| :--- | :--- | :--- |",
    ]
    for m in std["mappings"]:
        notes_str = ", ".join(m["modification_notes"]) or "Unchanged"
        lines.append(f"| `{m['original_name']}` | `{m['standardized_name']}` | {notes_str} |")

    lines.extend([
        "",
        "## 3. Executed Transformation Audit Trail",
        "| Version | Operation | Target Columns | Rows (Before→After) | Missing (Before→After) | Validated | Notes |",
        "| :---: | :--- | :--- | :---: | :---: | :---: | :--- |",
    ])
    for step in payload["transformation_audit_trail"]:
        cols_str = ", ".join(step["columns"]) if step["columns"] else "All"
        notes_str = "; ".join(step["notes"])
        lines.append(
            f"| v{step['version']} | `{step['operation']}` | `{cols_str}` | "
            f"{step['rows_before']}→{step['rows_after']} | {step['missing_before']}→{step['missing_after']} | "
            f"{'Yes' if step['validation_passed'] else 'No'} | {notes_str} |"
        )

    lines.extend([
        "",
        f"## 4. Remaining Quality Findings ({qual['total_issues_found']})",
    ])
    if not qual["issues"]:
        lines.append("No remaining data-quality issues detected.")
    else:
        for issue in qual["issues"]:
            lines.append(
                f"- **[{issue['severity'].upper()}] {issue['title']}** ({', '.join(issue['affected_columns'])}): {issue['description']}"
            )

    return "\n".join(lines)


def _render_html_report(payload: dict[str, Any]) -> str:
    comp = payload["before_after_summary"]
    qual = payload["current_quality_analysis"]
    steps_rows = ""
    for step in payload["transformation_audit_trail"]:
        cols_str = ", ".join(step["columns"]) if step["columns"] else "All Columns"
        notes_str = " • ".join(step["notes"])
        steps_rows += f"""
        <tr>
          <td><strong>v{step['version']}</strong></td>
          <td><code>{step['operation']}</code></td>
          <td><code>{cols_str}</code></td>
          <td>{step['rows_before']} → <strong>{step['rows_after']}</strong></td>
          <td>{step['missing_before']} → <strong>{step['missing_after']}</strong></td>
          <td style="color:#20309A;font-weight:700;">{"Verified" if step["validation_passed"] else "Failed"}</td>
          <td>{notes_str}</td>
        </tr>
        """

    issues_rows = ""
    for issue in qual["issues"]:
        issues_rows += f"""
        <tr>
          <td><code>{issue['issue_id']}</code></td>
          <td><span style="color:#BB232B;font-weight:700;text-transform:uppercase;">{issue['severity']}</span></td>
          <td><strong>{issue['title']}</strong></td>
          <td><code>{", ".join(issue['affected_columns'])}</code></td>
          <td>{issue['description']}</td>
        </tr>
        """
    if not issues_rows:
        issues_rows = '<tr><td colspan="5">All quality checks passed! Zero issues remaining.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Audit Report - {payload['original_filename']}</title>
  <style>
    body {{ font-family: 'Segoe UI', Inter, sans-serif; background: #F7F9FC; color: #0F172A; margin: 2rem; }}
    .header {{ background: #20309A; color: #FFFFFF; padding: 1.5rem 2rem; border-radius: 12px; border-bottom: 5px solid #BB232B; }}
    .card {{ background: #FFFFFF; border: 1px solid #D8E0F0; border-radius: 10px; padding: 1.25rem; margin-top: 1.5rem; }}
    h2 {{ color: #20309A; margin-top: 0; font-size: 1.15rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 0.75rem; font-size: 0.88rem; }}
    th {{ background: #20309A; color: #FFFFFF; text-align: left; padding: 0.65rem 0.85rem; }}
    td {{ padding: 0.6rem 0.85rem; border-bottom: 1px solid #D8E0F0; }}
    .kpi-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; }}
    .kpi {{ flex: 1; min-width: 160px; background: #EEF1FB; border-top: 4px solid #20309A; padding: 0.9rem; border-radius: 8px; }}
    .kpi.alert {{ background: #FDECEE; border-top-color: #BB232B; }}
  </style>
</head>
<body>
  <div class="header">
    <h1 style="margin:0;font-size:1.4rem;">Agentic AI Data Preprocessing & Quality Audit Report</h1>
    <p style="margin:0.35rem 0 0;color:#DCE4FF;font-size:0.9rem;">
      Dataset: <strong>{payload['original_filename']}</strong> | Snapshot: <strong>v{payload['current_snapshot_version']}</strong> | Generated: {payload['report_generated_at']}
    </p>
  </div>

  <div class="card">
    <h2>1. Before vs. After Preprocessing Summary</h2>
    <div class="kpi-row">
      <div class="kpi"><strong>Rows</strong><br/>{comp['rows_baseline']} → {comp['rows_current']} ({comp['rows_delta']})</div>
      <div class="kpi"><strong>Columns</strong><br/>{comp['cols_baseline']} → {comp['cols_current']} ({comp['cols_delta']})</div>
      <div class="kpi"><strong>Missing Cells</strong><br/>{comp['missing_baseline']} → {comp['missing_current']} ({comp['missing_delta']})</div>
      <div class="kpi"><strong>Exact Duplicates</strong><br/>{comp['duplicates_baseline']} → {comp['duplicates_current']} ({comp['duplicates_delta']})</div>
      <div class="kpi alert"><strong>Quality Risk Score</strong><br/>{comp['risk_score_baseline']}/100 → {comp['risk_score_current']}/100</div>
    </div>
  </div>

  <div class="card">
    <h2>2. Validated Preprocessing Audit Trail</h2>
    <table>
      <thead>
        <tr>
          <th>Version</th><th>Operation</th><th>Columns</th><th>Rows</th><th>Missing</th><th>Validation</th><th>Execution Notes</th>
        </tr>
      </thead>
      <tbody>{steps_rows}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>3. Remaining Data-Quality Findings ({qual['total_issues_found']})</h2>
    <table>
      <thead>
        <tr><th>ID</th><th>Severity</th><th>Issue</th><th>Affected Columns</th><th>Description</th></tr>
      </thead>
      <tbody>{issues_rows}</tbody>
    </table>
  </div>
</body>
</html>"""