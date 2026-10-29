import math
import re
from typing import Any
import numpy as np
import pandas as pd
from app.core.config import settings
from app.schemas.dataset import DatasetPreviewResponse
from app.schemas.profiling import (
    ColumnProfile,
    DatasetProfileResponse,
    FrequentValueItem,
    NumericStats,
    SemanticColumnType,
)
from app.services.session_store import DatasetSession


def to_json_safe(val: Any) -> Any:
    """Converts Pandas/NumPy values (NaN, NaT, Timestamp, numpy scalars) to JSON-safe Python primitives."""
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return round(float(val), 6)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return str(val)
    return str(val)


def format_bytes(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    kb = num_bytes / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"


def build_dataset_preview(df: pd.DataFrame, session: DatasetSession) -> DatasetPreviewResponse:
    head_df = df.head(settings.PREVIEW_ROWS)
    preview_rows: list[dict[str, Any]] = []

    for _, row in head_df.iterrows():
        row_dict = {col: to_json_safe(row[col]) for col in df.columns}
        preview_rows.append(row_dict)

    return DatasetPreviewResponse(
        dataset_id=session.dataset_id,
        filename=session.filename,
        file_format=session.file_format,
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=list(df.columns),
        preview_rows=preview_rows,
    )


def classify_semantic_type(series: pd.Series, col_name: str) -> SemanticColumnType:
    """
    Classifies a column into one of:
    numeric, categorical, boolean, datetime, identifier, text
    """
    non_null = series.dropna()
    total_non_null = len(non_null)

    if total_non_null == 0:
        return "categorical"

    # 1. Boolean check
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    if non_null.nunique(dropna=True) <= 2:
        lowered_vals = {str(v).strip().lower() for v in non_null.unique()}
        if lowered_vals.issubset({"true", "false", "yes", "no", "y", "n", "t", "f"}):
            return "boolean"

    # 2. Datetime check
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Check if string/object column represents dates
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        date_name_hint = bool(
            re.search(r"(?:^|_)(?:date|time|timestamp|dt|dob|created|updated)(?:$|_)", col_name)
        )
        sample = non_null.astype(str).head(100)
        # Only attempt date parsing if it looks like date strings or has a date column name
        looks_like_date = sample.str.contains(r"[\-/:\s]", regex=True).mean() > 0.7
        if date_name_hint or looks_like_date:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() >= 0.85:
                return "datetime"

    # 3. Identifier check
    unique_count = int(non_null.nunique(dropna=True))
    unique_ratio = unique_count / total_non_null if total_non_null > 0 else 0.0
    id_name_pattern = bool(
        re.search(r"(?:^|_)(?:id|uuid|guid|key|code|ssn|account_no|emp_no|invoice_no)(?:$|_\d+$)", col_name)
    )

    if id_name_pattern and unique_ratio >= 0.8:
        return "identifier"

    if (
        total_non_null >= 20
        and unique_ratio == 1.0
        and (pd.api.types.is_integer_dtype(series) or pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series))
    ):
        if pd.api.types.is_integer_dtype(series):
            return "identifier"
        avg_spaces = non_null.astype(str).head(100).str.count(" ").mean()
        if avg_spaces < 0.2:
            return "identifier"

    # 4. Numeric check
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # 5. Text vs Categorical check for string/object columns
    str_sample = non_null.astype(str).head(250)
    avg_len = float(str_sample.str.len().mean())
    avg_words = float(str_sample.str.split().str.len().mean())

    if avg_len > 45.0 or (avg_words >= 5.0 and unique_ratio > 0.4):
        return "text"

    return "categorical"


def profile_dataset(df: pd.DataFrame, session: DatasetSession) -> DatasetProfileResponse:
    """
    Dataset Profiling Agent:
    Generates comprehensive structural, statistical, and semantic metadata for a dataset.
    """
    row_count = int(len(df))
    col_count = int(len(df.columns))
    total_cells = row_count * col_count if row_count * col_count > 0 else 1

    memory_per_col = df.memory_usage(index=True, deep=True)
    total_memory_bytes = int(memory_per_col.sum())

    total_missing_cells = int(df.isna().sum().sum())
    total_missing_pct = round((total_missing_cells / total_cells) * 100, 2)

    exact_dups = int(df.duplicated().sum()) if row_count > 0 else 0
    exact_dups_pct = round((exact_dups / row_count) * 100, 2) if row_count > 0 else 0.0

    # Map standardized name back to original name
    std_to_orig = {
        item.standardized_name: item.original_name
        for item in session.standardization_report.mappings
    }

    semantic_type_counts: dict[str, int] = {
        "numeric": 0,
        "categorical": 0,
        "boolean": 0,
        "datetime": 0,
        "identifier": 0,
        "text": 0,
    }

    column_profiles: list[ColumnProfile] = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        non_null_count = row_count - null_count
        null_pct = round((null_count / row_count) * 100, 2) if row_count > 0 else 0.0

        unique_count = int(series.nunique(dropna=True))
        unique_pct = round((unique_count / non_null_count) * 100, 2) if non_null_count > 0 else 0.0

        sem_type = classify_semantic_type(series, col)
        semantic_type_counts[sem_type] = semantic_type_counts.get(sem_type, 0) + 1

        # Sample up to 5 non-null unique values
        sample_vals = [to_json_safe(v) for v in series.dropna().unique()[:5]]

        # Numeric statistics if column is numeric in Pandas
        num_stats: NumericStats | None = None
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            clean_num = pd.to_numeric(series, errors="coerce").dropna()
            if len(clean_num) > 0:
                q25, median, q75 = np.percentile(clean_num, [25, 50, 75])
                skew_val = float(clean_num.skew()) if len(clean_num) > 2 else 0.0
                num_stats = NumericStats(
                    mean=to_json_safe(clean_num.mean()),
                    std=to_json_safe(clean_num.std()) if len(clean_num) > 1 else 0.0,
                    min=to_json_safe(clean_num.min()),
                    q25=to_json_safe(q25),
                    median=to_json_safe(median),
                    q75=to_json_safe(q75),
                    max=to_json_safe(clean_num.max()),
                    skewness=to_json_safe(skew_val),
                    zeros_count=int((clean_num == 0).sum()),
                    negative_count=int((clean_num < 0).sum()),
                )

        # Frequent categorical/discrete values (top 5)
        top_values: list[FrequentValueItem] = []
        if non_null_count > 0:
            val_counts = series.dropna().astype(str).value_counts().head(5)
            for val_str, cnt in val_counts.items():
                top_values.append(
                    FrequentValueItem(
                        value=str(val_str)[:80],
                        count=int(cnt),
                        percentage=round((int(cnt) / non_null_count) * 100, 2),
                    )
                )

        column_profiles.append(
            ColumnProfile(
                name=col,
                original_name=std_to_orig.get(col, col),
                pandas_dtype=str(series.dtype),
                semantic_type=sem_type,
                total_count=row_count,
                null_count=null_count,
                null_percentage=null_pct,
                non_null_count=non_null_count,
                unique_count=unique_count,
                unique_percentage=unique_pct,
                memory_bytes=int(memory_per_col.get(col, 0)),
                sample_values=sample_vals,
                numeric_stats=num_stats,
                top_values=top_values,
            )
        )

    return DatasetProfileResponse(
        dataset_id=session.dataset_id,
        filename=session.filename,
        row_count=row_count,
        column_count=col_count,
        memory_usage_bytes=total_memory_bytes,
        memory_usage_human=format_bytes(total_memory_bytes),
        total_missing_cells=total_missing_cells,
        total_missing_percentage=total_missing_pct,
        exact_duplicate_rows=exact_dups,
        exact_duplicate_percentage=exact_dups_pct,
        semantic_type_counts=semantic_type_counts,
        column_profiles=column_profiles,
    )