import re
from typing import Any
import pandas as pd
from app.schemas.dataset import ColumnMappingItem, ColumnStandardizationReport


def standardize_column_names(df: pd.DataFrame) -> tuple[pd.DataFrame, ColumnStandardizationReport]:
    """
    Standardizes DataFrame column names deterministically according to rules:
    1. Convert to lowercase
    2. Trim leading/trailing whitespace
    3. Replace spaces, hyphens, and separators with underscores
    4. Remove unnecessary special characters (e.g., $, %, parentheses)
    5. Collapse repeated underscores
    6. Strip leading/trailing underscores
    7. Assign safe names to empty/unnamed columns
    8. Resolve duplicates sequentially (col, col_2, col_3)
    9. Preserve column order and return original-to-standardized mapping
    """
    raw_columns: list[Any] = list(df.columns)
    used_names: set[str] = set()
    base_name_counts: dict[str, int] = {}

    mappings: list[ColumnMappingItem] = []
    original_to_standardized: dict[str, str] = {}
    new_columns: list[str] = []

    modified_count = 0
    duplicate_names_resolved = 0
    empty_names_filled = 0

    for idx, raw_col in enumerate(raw_columns):
        original_str = "" if raw_col is None else str(raw_col)
        notes: list[str] = []

        # Detect empty or Pandas auto-generated "Unnamed: X" headers
        trimmed = original_str.strip()
        is_unnamed = (
            trimmed == ""
            or bool(re.match(r"^unnamed:\s*\d+$", trimmed, flags=re.IGNORECASE))
        )

        if is_unnamed:
            base_clean = f"unnamed_col_{idx + 1}"
            empty_names_filled += 1
            notes.append("Assigned safe name to empty/unnamed column")
        else:
            if trimmed != original_str:
                notes.append("Trimmed whitespace")

            lowered = trimmed.lower()
            if lowered != trimmed:
                notes.append("Converted to lowercase")

            # Replace spaces, hyphens, slashes, and dots with underscores
            sep_normalized = re.sub(r"[\s\-\./\\]+", "_", lowered)
            if sep_normalized != lowered:
                notes.append("Normalized spaces/separators to underscores")

            # Remove special characters (keep only a-z, 0-9, and underscore)
            alnum_only = re.sub(r"[^a-z0-9_]", "", sep_normalized)
            if alnum_only != sep_normalized:
                notes.append("Removed special characters")

            # Collapse multiple underscores and strip leading/trailing underscores
            collapsed = re.sub(r"_+", "_", alnum_only).strip("_")
            if not collapsed:
                base_clean = f"unnamed_col_{idx + 1}"
                empty_names_filled += 1
                notes.append("Assigned safe name after symbol removal")
            elif collapsed[0].isdigit():
                base_clean = f"col_{collapsed}"
                notes.append("Prefixed leading digit with 'col_'")
            else:
                base_clean = collapsed

        # Resolve duplicates deterministically
        if base_clean not in used_names:
            final_name = base_clean
            base_name_counts[base_clean] = 1
        else:
            duplicate_names_resolved += 1
            suffix_num = base_name_counts.get(base_clean, 1) + 1
            candidate = f"{base_clean}_{suffix_num}"
            while candidate in used_names:
                suffix_num += 1
                candidate = f"{base_clean}_{suffix_num}"
            base_name_counts[base_clean] = suffix_num
            final_name = candidate
            notes.append(f"Resolved duplicate column name as '{final_name}'")

        used_names.add(final_name)
        new_columns.append(final_name)

        was_modified = original_str != final_name
        if was_modified:
            modified_count += 1

        # Handle duplicate original keys in dictionary representation gracefully
        dict_key = original_str if original_str not in original_to_standardized else f"{original_str} (col {idx + 1})"
        original_to_standardized[dict_key] = final_name

        mappings.append(
            ColumnMappingItem(
                index=idx,
                original_name=original_str,
                standardized_name=final_name,
                was_modified=was_modified,
                modification_notes=notes,
            )
        )

    standardized_df = df.copy()
    standardized_df.columns = new_columns

    report = ColumnStandardizationReport(
        total_columns=len(new_columns),
        modified_count=modified_count,
        duplicate_names_resolved=duplicate_names_resolved,
        empty_names_filled=empty_names_filled,
        mappings=mappings,
        original_to_standardized=original_to_standardized,
    )

    return standardized_df, report