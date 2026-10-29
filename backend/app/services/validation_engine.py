import numpy as np
import pandas as pd
from app.core.exceptions import DatasetError
from app.schemas.transformations import (
    TransformationRequest,
    ValidationCheckItem,
    ValidationReport,
)


def validate_transformation_result(
    before_df: pd.DataFrame,
    after_df: pd.DataFrame,
    request: TransformationRequest,
) -> ValidationReport:
    """
    Validation Agent:
    Verifies post-transformation dataset integrity and operation invariants
    before allowing any state change to be committed.
    """
    checks: list[ValidationCheckItem] = []

    # Check 1: Non-empty dataset invariant
    non_empty = len(after_df) > 0 and len(after_df.columns) > 0
    checks.append(
        ValidationCheckItem(
            check_name="non_empty_dataset",
            passed=non_empty,
            details=f"Resulting dataset has {len(after_df):,} rows and {len(after_df.columns)} columns.",
        )
    )

    # Check 2: No infinite values introduced in numeric columns
    numeric_cols = after_df.select_dtypes(include=[np.number]).columns
    inf_count = 0
    for col in numeric_cols:
        inf_count += int(np.isinf(after_df[col].dropna()).sum())

    checks.append(
        ValidationCheckItem(
            check_name="no_infinite_values",
            passed=(inf_count == 0),
            details="No Inf/-Inf values detected in numeric columns."
            if inf_count == 0
            else f"Found {inf_count} infinite values in numeric columns.",
        )
    )

    # Check 3: Operation-specific invariant verification
    op = request.operation
    if op in ("impute_numeric_mean", "impute_numeric_median", "impute_categorical_mode", "impute_constant"):
        remaining_nulls = sum(int(after_df[c].isna().sum()) for c in request.columns if c in after_df.columns)
        checks.append(
            ValidationCheckItem(
                check_name="imputation_completeness",
                passed=(remaining_nulls == 0),
                details=f"Target columns {request.columns} have {remaining_nulls} missing values after imputation.",
            )
        )
    elif op == "remove_exact_duplicates":
        rem_dups = int(after_df.duplicated().sum())
        checks.append(
            ValidationCheckItem(
                check_name="deduplication_completeness",
                passed=(rem_dups == 0),
                details=f"Dataset has {rem_dups} exact duplicate rows remaining.",
            )
        )
    elif op == "drop_columns":
        still_present = [c for c in request.columns if c in after_df.columns]
        checks.append(
            ValidationCheckItem(
                check_name="columns_dropped_verification",
                passed=(len(still_present) == 0),
                details=f"Dropped columns absent from schema: {len(still_present) == 0}.",
            )
        )
    elif op == "convert_to_numeric":
        all_numeric = all(pd.api.types.is_numeric_dtype(after_df[c]) for c in request.columns if c in after_df.columns)
        checks.append(
            ValidationCheckItem(
                check_name="numeric_dtype_verification",
                passed=all_numeric,
                details=f"Target columns {request.columns} converted to numeric dtypes.",
            )
        )
    elif op == "apply_scaler":
        all_scaled = all(pd.api.types.is_numeric_dtype(after_df[c]) for c in request.columns if c in after_df.columns)
        checks.append(
            ValidationCheckItem(
                check_name="scaler_integrity",
                passed=all_scaled,
                details=f"Scaled columns {request.columns} maintained finite numeric values.",
            )
        )
    else:
        checks.append(
            ValidationCheckItem(
                check_name="schema_consistency",
                passed=(len(after_df.columns) == len(set(after_df.columns))),
                details="All resulting column names are unique and valid.",
            )
        )

    is_valid = all(c.passed for c in checks)
    if not is_valid:
        failed_reasons = "; ".join(f"{c.check_name}: {c.details}" for c in checks if not c.passed)
        raise DatasetError(
            f"Validation Agent blocked operation '{op}': {failed_reasons}",
            status_code=422,
        )

    return ValidationReport(is_valid=is_valid, checks=checks)