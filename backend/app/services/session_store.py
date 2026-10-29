from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid
import pandas as pd
from app.core.config import settings
from app.core.exceptions import DatasetError
from app.schemas.dataset import ColumnStandardizationReport


@dataclass
class AuditRecord:
    version: int
    timestamp: str
    operation: str
    columns: list[str]
    parameters: dict[str, Any]
    rows_before: int
    rows_after: int
    cols_before: int
    cols_after: int
    missing_before: int
    missing_after: int
    validation_passed: bool
    notes: list[str]


@dataclass
class DatasetSession:
    dataset_id: str
    filename: str
    file_format: str
    file_size_bytes: int
    original_file_path: Path
    current_snapshot_path: Path
    current_version: int
    standardization_report: ColumnStandardizationReport
    history_snapshots: list[Path] = field(default_factory=list)
    audit_log: list[AuditRecord] = field(default_factory=list)


class SessionStore:
    """
    Manages uploaded dataset sessions, disk-backed recoverable snapshots,
    and full undo/restore version control.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, DatasetSession] = {}

    def create_session(
        self,
        filename: str,
        file_format: str,
        raw_bytes: bytes,
        standardized_df: pd.DataFrame,
        standardization_report: ColumnStandardizationReport,
    ) -> DatasetSession:
        dataset_id = str(uuid.uuid4())

        safe_ext = Path(filename).suffix.lower()
        original_path = settings.ORIGINALS_DIR / f"{dataset_id}_original{safe_ext}"
        original_path.write_bytes(raw_bytes)

        snapshot_path = settings.SNAPSHOTS_DIR / f"{dataset_id}_v0.pkl"
        standardized_df.to_pickle(snapshot_path)

        initial_missing = int(standardized_df.isna().sum().sum())
        initial_audit = AuditRecord(
            version=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation="standardize_column_names",
            columns=list(standardized_df.columns),
            parameters={"auto_on_upload": True},
            rows_before=len(standardized_df),
            rows_after=len(standardized_df),
            cols_before=len(standardized_df.columns),
            cols_after=len(standardized_df.columns),
            missing_before=initial_missing,
            missing_after=initial_missing,
            validation_passed=True,
            notes=[f"Standardized {standardization_report.modified_count} column headers on initial upload."],
        )

        session = DatasetSession(
            dataset_id=dataset_id,
            filename=filename,
            file_format=file_format.lstrip(".").upper(),
            file_size_bytes=len(raw_bytes),
            original_file_path=original_path,
            current_snapshot_path=snapshot_path,
            current_version=0,
            standardization_report=standardization_report,
            history_snapshots=[snapshot_path],
            audit_log=[initial_audit],
        )
        self._sessions[dataset_id] = session
        return session

    def get_session(self, dataset_id: str) -> DatasetSession:
        session = self._sessions.get(dataset_id)
        if not session:
            raise DatasetError(
                f"Dataset session '{dataset_id}' not found. Please upload the dataset again.",
                status_code=404,
            )
        return session

    def load_dataframe(self, dataset_id: str) -> pd.DataFrame:
        session = self.get_session(dataset_id)
        if not session.current_snapshot_path.exists():
            raise DatasetError(
                f"Snapshot file for dataset '{dataset_id}' is missing on disk.",
                status_code=404,
            )
        return pd.read_pickle(session.current_snapshot_path)

    def load_version_dataframe(self, dataset_id: str, version: int) -> pd.DataFrame:
        session = self.get_session(dataset_id)
        if version < 0 or version >= len(session.history_snapshots):
            raise DatasetError(f"Snapshot version {version} does not exist.", status_code=404)
        path = session.history_snapshots[version]
        return pd.read_pickle(path)

    def save_new_snapshot(
        self,
        dataset_id: str,
        new_df: pd.DataFrame,
        operation: str,
        columns: list[str],
        parameters: dict[str, Any],
        rows_before: int,
        cols_before: int,
        missing_before: int,
        missing_after: int,
        validation_passed: bool,
        notes: list[str],
    ) -> int:
        session = self.get_session(dataset_id)

        # If user undid steps previously and now branches, trim future snapshots
        if session.current_version < len(session.history_snapshots) - 1:
            session.history_snapshots = session.history_snapshots[: session.current_version + 1]
            session.audit_log = session.audit_log[: session.current_version + 1]

        next_version = len(session.history_snapshots)
        snapshot_path = settings.SNAPSHOTS_DIR / f"{dataset_id}_v{next_version}.pkl"
        new_df.to_pickle(snapshot_path)

        session.history_snapshots.append(snapshot_path)
        session.current_snapshot_path = snapshot_path
        session.current_version = next_version

        session.audit_log.append(
            AuditRecord(
                version=next_version,
                timestamp=datetime.now(timezone.utc).isoformat(),
                operation=operation,
                columns=columns,
                parameters=parameters,
                rows_before=rows_before,
                rows_after=len(new_df),
                cols_before=cols_before,
                cols_after=len(new_df.columns),
                missing_before=missing_before,
                missing_after=missing_after,
                validation_passed=validation_passed,
                notes=notes,
            )
        )
        return next_version

    def undo_last_snapshot(self, dataset_id: str) -> int:
        session = self.get_session(dataset_id)
        if session.current_version <= 0:
            raise DatasetError("Already at the initial dataset state (v0); nothing to undo.", status_code=400)

        target_version = session.current_version - 1
        session.current_version = target_version
        session.current_snapshot_path = session.history_snapshots[target_version]
        session.history_snapshots = session.history_snapshots[: target_version + 1]
        session.audit_log = session.audit_log[: target_version + 1]
        return target_version

    def restore_snapshot_version(self, dataset_id: str, target_version: int) -> int:
        session = self.get_session(dataset_id)
        if target_version < 0 or target_version >= len(session.history_snapshots):
            raise DatasetError(
                f"Invalid version {target_version}. Available versions: 0 to {len(session.history_snapshots) - 1}.",
                status_code=400,
            )

        session.current_version = target_version
        session.current_snapshot_path = session.history_snapshots[target_version]
        session.history_snapshots = session.history_snapshots[: target_version + 1]
        session.audit_log = session.audit_log[: target_version + 1]
        return target_version


session_store = SessionStore()