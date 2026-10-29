from app.schemas.transformations import (
    AuditHistoryResponse,
    AuditLogEntrySchema,
    BeforeAfterComparisonResponse,
)
from app.services.profiler import to_json_safe
from app.services.quality_analyzer import analyze_dataset_quality
from app.services.session_store import session_store


def get_audit_history(dataset_id: str) -> AuditHistoryResponse:
    session = session_store.get_session(dataset_id)
    entries = [
        AuditLogEntrySchema(
            version=rec.version,
            timestamp=rec.timestamp,
            operation=rec.operation,
            columns=rec.columns,
            parameters=rec.parameters,
            rows_before=rec.rows_before,
            rows_after=rec.rows_after,
            cols_before=rec.cols_before,
            cols_after=rec.cols_after,
            missing_before=rec.missing_before,
            missing_after=rec.missing_after,
            validation_passed=rec.validation_passed,
            notes=rec.notes,
        )
        for rec in session.audit_log
    ]
    return AuditHistoryResponse(
        dataset_id=dataset_id,
        current_version=session.current_version,
        total_versions=len(session.history_snapshots),
        can_undo=session.current_version > 0,
        entries=entries,
    )


def build_before_after_comparison(dataset_id: str) -> BeforeAfterComparisonResponse:
    """
    Compares the initial standardized dataset (v0) against the current active snapshot (vN).
    """
    session = session_store.get_session(dataset_id)
    base_df = session_store.load_version_dataframe(dataset_id, 0)
    curr_df = session_store.load_dataframe(dataset_id)

    base_quality = analyze_dataset_quality(base_df)
    curr_quality = analyze_dataset_quality(curr_df)

    rows_base = int(len(base_df))
    rows_curr = int(len(curr_df))
    cols_base = int(len(base_df.columns))
    cols_curr = int(len(curr_df.columns))

    missing_base = int(base_df.isna().sum().sum())
    missing_curr = int(curr_df.isna().sum().sum())

    dups_base = int(base_df.duplicated().sum()) if rows_base > 0 else 0
    dups_curr = int(curr_df.duplicated().sum()) if rows_curr > 0 else 0

    base_cols_set = set(base_df.columns)
    curr_cols_set = set(curr_df.columns)
    added_cols = [c for c in curr_df.columns if c not in base_cols_set]
    removed_cols = [c for c in base_df.columns if c not in curr_cols_set]

    baseline_sample = [
        {c: to_json_safe(row[c]) for c in base_df.columns}
        for _, row in base_df.head(5).iterrows()
    ]
    current_sample = [
        {c: to_json_safe(row[c]) for c in curr_df.columns}
        for _, row in curr_df.head(5).iterrows()
    ]

    return BeforeAfterComparisonResponse(
        dataset_id=dataset_id,
        baseline_version=0,
        current_version=session.current_version,
        rows_baseline=rows_base,
        rows_current=rows_curr,
        rows_delta=rows_curr - rows_base,
        cols_baseline=cols_base,
        cols_current=cols_curr,
        cols_delta=cols_curr - cols_base,
        missing_baseline=missing_base,
        missing_current=missing_curr,
        missing_delta=missing_curr - missing_base,
        duplicates_baseline=dups_base,
        duplicates_current=dups_curr,
        duplicates_delta=dups_curr - dups_base,
        risk_score_baseline=base_quality.risk_score,
        risk_score_current=curr_quality.risk_score,
        risk_score_delta=curr_quality.risk_score - base_quality.risk_score,
        added_columns=added_cols,
        removed_columns=removed_cols,
        baseline_sample=baseline_sample,
        current_sample=current_sample,
    )