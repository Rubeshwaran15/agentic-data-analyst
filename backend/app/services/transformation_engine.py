from typing import Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from app.core.exceptions import DatasetError
from app.schemas.transformations import (
    MLPipelineRequest,
    TransformationEffectSummary,
    TransformationRequest,
)
from app.services.column_normalizer import standardize_column_names
from app.services.profiler import classify_semantic_type, to_json_safe


def _validate_target_columns(df: pd.DataFrame, columns: list[str], require_non_empty: bool = True) -> list[str]:
    if require_non_empty and not columns:
        raise DatasetError("This operation requires at least one target column.", status_code=400)

    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise DatasetError(
            f"Columns not found in dataset: {missing}",
            status_code=400,
            details={"missing_columns": missing, "available_columns": list(df.columns)},
        )
    return columns


def _protect_identifiers(df: pd.DataFrame, columns: list[str], parameters: dict[str, Any]) -> list[str]:
    if parameters.get("allow_identifier_transform", False):
        return columns

    safe_cols: list[str] = []
    for col in columns:
        sem_type = classify_semantic_type(df[col], col)
        if sem_type != "identifier":
            safe_cols.append(col)

    if not safe_cols and columns:
        raise DatasetError(
            f"Selected column(s) {columns} are classified as identifiers and are protected by default.",
            status_code=400,
        )
    return safe_cols


def apply_allowlisted_operation(
    df: pd.DataFrame, request: TransformationRequest
) -> tuple[pd.DataFrame, list[str]]:
    work_df = df.copy()
    op = request.operation
    params = request.parameters or {}
    notes: list[str] = []

    if op == "standardize_column_names":
        work_df, report = standardize_column_names(work_df)
        notes.append(f"Standardized {report.modified_count} column headers.")
        return work_df, notes

    if op == "remove_exact_duplicates":
        before = len(work_df)
        work_df = work_df.drop_duplicates().reset_index(drop=True)
        removed = before - len(work_df)
        notes.append(f"Removed {removed:,} exact duplicate rows.")
        return work_df, notes

    if op == "remove_empty_rows":
        before = len(work_df)
        work_df = work_df.dropna(how="all").reset_index(drop=True)
        removed = before - len(work_df)
        notes.append(f"Removed {removed:,} completely empty rows.")
        return work_df, notes

    if op == "drop_columns":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        work_df = work_df.drop(columns=cols)
        notes.append(f"Dropped {len(cols)} column(s): {', '.join(cols)}.")
        return work_df, notes

    if op in ("impute_numeric_mean", "impute_numeric_median"):
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)

        if request.use_ml_train_test_split and len(work_df) >= 10:
            train_idx, _ = train_test_split(work_df.index, train_size=request.train_size, random_state=42)
            fit_df = work_df.loc[train_idx]
            notes.append(f"Fit imputer on {len(train_idx):,} training rows ({int(request.train_size * 100)}% split).")
        else:
            fit_df = work_df

        for col in cols:
            numeric_series = pd.to_numeric(work_df[col], errors="coerce")
            fit_series = pd.to_numeric(fit_df[col], errors="coerce").dropna()
            if fit_series.empty:
                raise DatasetError(f"Column '{col}' has no valid numeric values to compute {op}.", status_code=400)

            fill_val = float(fit_series.mean()) if op == "impute_numeric_mean" else float(fit_series.median())
            nulls_before = int(numeric_series.isna().sum())
            work_df[col] = numeric_series.fillna(round(fill_val, 6))
            notes.append(f"Imputed {nulls_before:,} missing values in '{col}' with {round(fill_val, 4)}.")
        return work_df, notes

    if op == "impute_categorical_mode":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)

        for col in cols:
            non_null = work_df[col].dropna()
            if non_null.empty:
                raise DatasetError(f"Column '{col}' is completely empty; cannot compute mode.", status_code=400)
            mode_val = non_null.mode().iloc[0]
            nulls_before = int(work_df[col].isna().sum())
            work_df[col] = work_df[col].fillna(mode_val)
            notes.append(f"Imputed {nulls_before:,} missing values in '{col}' using mode '{mode_val}'.")
        return work_df, notes

    if op == "impute_constant":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        fill_value = params.get("fill_value", "Unknown")
        for col in cols:
            nulls_before = int(work_df[col].isna().sum())
            work_df[col] = work_df[col].fillna(fill_value)
            notes.append(f"Imputed {nulls_before:,} missing values in '{col}' with constant '{fill_value}'.")
        return work_df, notes

    if op == "normalize_text":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        trim_ws = bool(params.get("trim_whitespace", True))
        case_mode = str(params.get("case_mode", "title")).lower()

        for col in cols:
            mask = work_df[col].notna()
            s = work_df.loc[mask, col].astype(str)
            if trim_ws:
                s = s.str.strip().str.replace(r"\s+", " ", regex=True)
            if case_mode == "lower":
                s = s.str.lower()
            elif case_mode == "upper":
                s = s.str.upper()
            elif case_mode == "title" and bool(params.get("normalize_case", True)):
                s = s.str.title()
            work_df.loc[mask, col] = s
            notes.append(f"Normalized text in '{col}' (trim={trim_ws}, case={case_mode}).")
        return work_df, notes

    if op in ("convert_to_numeric", "convert_data_type"):
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        target_dtype = str(params.get("target_dtype", "numeric")).lower()

        for col in cols:
            if op == "convert_to_numeric" or target_dtype in ("numeric", "float", "int"):
                cleaned = work_df[col].astype(str).str.replace(r"[\$,\s]", "", regex=True)
                cleaned = cleaned.replace({"nan": np.nan, "None": np.nan, "": np.nan})
                work_df[col] = pd.to_numeric(cleaned, errors="coerce")
                notes.append(f"Converted '{col}' to numeric dtype ({work_df[col].dtype}).")
            elif target_dtype == "datetime":
                work_df[col] = pd.to_datetime(work_df[col], errors="coerce", format="mixed")
                notes.append(f"Converted '{col}' to datetime.")
            elif target_dtype in ("string", "categorical"):
                work_df[col] = work_df[col].astype("string")
                notes.append(f"Converted '{col}' to string/categorical.")
            elif target_dtype == "boolean":
                mapping = {"true": True, "false": False, "1": True, "0": False, "yes": True, "no": False}
                work_df[col] = work_df[col].astype(str).str.strip().str.lower().map(mapping)
                notes.append(f"Converted '{col}' to boolean.")
            else:
                raise DatasetError(f"Unsupported target_dtype '{target_dtype}'.", status_code=400)
        return work_df, notes

    if op in ("detect_outliers", "cap_outliers"):
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)
        iqr_multiplier = float(params.get("iqr_multiplier", 1.5))

        for col in cols:
            series = pd.to_numeric(work_df[col], errors="coerce")
            clean = series.dropna()
            if len(clean) < 4:
                continue
            q25, q75 = np.percentile(clean, [25, 75])
            iqr = q75 - q25
            lower = float(params.get("lower_bound", q25 - iqr_multiplier * iqr))
            upper = float(params.get("upper_bound", q75 + iqr_multiplier * iqr))
            outlier_mask = (series < lower) | (series > upper)
            outlier_count = int(outlier_mask.sum())

            if op == "detect_outliers":
                work_df[f"{col}_is_outlier"] = outlier_mask.fillna(False)
                notes.append(f"Flagged {outlier_count:,} outliers in '{col}' outside [{round(lower, 2)}, {round(upper, 2)}].")
            else:
                work_df[col] = series.clip(lower=lower, upper=upper)
                notes.append(f"Capped {outlier_count:,} outliers in '{col}' to bounds [{round(lower, 2)}, {round(upper, 2)}].")
        return work_df, notes

    if op == "remove_outliers":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)
        iqr_multiplier = float(params.get("iqr_multiplier", 1.5))
        before = len(work_df)

        keep_mask = pd.Series(True, index=work_df.index)
        for col in cols:
            series = pd.to_numeric(work_df[col], errors="coerce")
            clean = series.dropna()
            if len(clean) < 4:
                continue
            q25, q75 = np.percentile(clean, [25, 75])
            iqr = q75 - q25
            lower = float(params.get("lower_bound", q25 - iqr_multiplier * iqr))
            upper = float(params.get("upper_bound", q75 + iqr_multiplier * iqr))
            keep_mask &= series.isna() | ((series >= lower) & (series <= upper))

        work_df = work_df.loc[keep_mask].reset_index(drop=True)
        notes.append(f"Removed {before - len(work_df):,} outlier rows across {cols}.")
        return work_df, notes

    if op == "one_hot_encode":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)
        drop_first = bool(params.get("drop_first", False))

        for col in cols:
            if work_df[col].nunique(dropna=True) > 25:
                raise DatasetError(
                    f"Column '{col}' has >25 unique categories. One-hot encoding blocked to prevent memory explosion.",
                    status_code=400,
                )
        work_df = pd.get_dummies(work_df, columns=cols, drop_first=drop_first, dtype=int)
        notes.append(f"One-hot encoded column(s): {', '.join(cols)}.")
        return work_df, notes

    if op == "ordinal_encode":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        categories_order: list[str] = params.get("categories_order", [])
        if not categories_order:
            raise DatasetError(
                "Ordinal encoding requires an explicit 'categories_order' list in parameters.",
                status_code=400,
            )
        order_map = {str(val).strip().lower(): idx for idx, val in enumerate(categories_order)}
        for col in cols:
            work_df[col] = (
                work_df[col]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(order_map)
            )
            notes.append(f"Ordinal encoded '{col}' using explicit order {categories_order}.")
        return work_df, notes

    if op == "apply_scaler":
        cols = _validate_target_columns(work_df, request.columns, require_non_empty=True)
        cols = _protect_identifiers(work_df, cols, params)
        method = str(params.get("method", "standard")).lower()

        scaler_map = {
            "standard": StandardScaler(),
            "minmax": MinMaxScaler(),
            "robust": RobustScaler(),
        }
        scaler = scaler_map.get(method)
        if scaler is None:
            raise DatasetError(f"Unsupported scaler method '{method}'. Choose standard, minmax, or robust.", status_code=400)

        for col in cols:
            if not pd.api.types.is_numeric_dtype(work_df[col]):
                raise DatasetError(f"Column '{col}' must be numeric before scaling.", status_code=400)
            if work_df[col].isna().any():
                raise DatasetError(
                    f"Column '{col}' contains missing values. Impute missing values before applying {method} scaler.",
                    status_code=400,
                )

        if request.use_ml_train_test_split and len(work_df) >= 10:
            train_idx, _ = train_test_split(work_df.index, train_size=request.train_size, random_state=42)
            scaler.fit(work_df.loc[train_idx, cols])
            work_df[cols] = np.round(scaler.transform(work_df[cols]), 6)
            notes.append(f"Fit {method} scaler on training split ({int(request.train_size * 100)}%) and transformed {cols}.")
        else:
            work_df[cols] = np.round(scaler.fit_transform(work_df[cols]), 6)
            notes.append(f"Applied {method} scaler to {cols}.")
        return work_df, notes

    raise DatasetError(f"Operation '{op}' is not in the allowlisted registry.", status_code=400)


def preview_transformation_effect(
    df: pd.DataFrame, request: TransformationRequest
) -> tuple[pd.DataFrame, TransformationEffectSummary]:
    rows_before = int(len(df))
    cols_before = int(len(df.columns))
    missing_before = int(df.isna().sum().sum())

    transformed_df, notes = apply_allowlisted_operation(df, request)

    rows_after = int(len(transformed_df))
    cols_after = int(len(transformed_df.columns))
    missing_after = int(transformed_df.isna().sum().sum())

    sample_before = [
        {c: to_json_safe(row[c]) for c in df.columns}
        for _, row in df.head(5).iterrows()
    ]
    sample_after = [
        {c: to_json_safe(row[c]) for c in transformed_df.columns}
        for _, row in transformed_df.head(5).iterrows()
    ]

    effect = TransformationEffectSummary(
        operation=request.operation,
        target_columns=request.columns,
        rows_before=rows_before,
        rows_after=rows_after,
        rows_delta=rows_after - rows_before,
        cols_before=cols_before,
        cols_after=cols_after,
        cols_delta=cols_after - cols_before,
        missing_before=missing_before,
        missing_after=missing_after,
        missing_delta=missing_after - missing_before,
        execution_notes=notes,
        sample_before=sample_before,
        sample_after=sample_after,
    )
    return transformed_df, effect


def execute_leak_free_ml_pipeline(
    df: pd.DataFrame, config: MLPipelineRequest
) -> tuple[pd.DataFrame, int, int, list[str], list[str]]:
    if len(df) < 6:
        raise DatasetError("Dataset must have at least 6 rows to run a train/test split ML pipeline.", status_code=400)

    work_df = df.drop_duplicates().reset_index(drop=True)
    steps_applied: list[str] = []
    preserved_ids: list[str] = []

    if len(work_df) < len(df):
        steps_applied.append(f"Removed {len(df) - len(work_df)} exact duplicate rows prior to splitting.")

    if config.drop_constant_columns:
        const_cols = [
            c for c in work_df.columns
            if c != config.target_column and work_df[c].dropna().nunique() <= 1
        ]
        if const_cols:
            work_df = work_df.drop(columns=const_cols)
            steps_applied.append(f"Dropped constant column(s): {', '.join(const_cols)}.")

    feature_numeric_cols: list[str] = []
    feature_cat_cols: list[str] = []

    for col in work_df.columns:
        if col == config.target_column or col == "ml_split":
            continue
        sem_type = classify_semantic_type(work_df[col], col)
        if sem_type == "identifier":
            preserved_ids.append(col)
        elif sem_type == "numeric":
            feature_numeric_cols.append(col)
        elif sem_type == "categorical" and work_df[col].nunique(dropna=True) <= 15:
            feature_cat_cols.append(col)

    train_idx, test_idx = train_test_split(
        work_df.index, train_size=config.train_size, random_state=42
    )
    work_df["ml_split"] = "test"
    work_df.loc[train_idx, "ml_split"] = "train"
    steps_applied.append(
        f"Partitioned dataset into {len(train_idx)} train rows and {len(test_idx)} test rows ({int(config.train_size * 100)}/{int((1 - config.train_size) * 100)} split)."
    )

    for col in feature_numeric_cols:
        train_series = pd.to_numeric(work_df.loc[train_idx, col], errors="coerce").dropna()
        if train_series.empty:
            continue
        fill_val = (
            float(train_series.median())
            if config.numeric_impute_strategy == "median"
            else float(train_series.mean())
        )
        if work_df[col].isna().any():
            work_df[col] = pd.to_numeric(work_df[col], errors="coerce").fillna(round(fill_val, 6))
            steps_applied.append(
                f"Fit {config.numeric_impute_strategy} imputer on Train for '{col}' (fill={round(fill_val, 4)})."
            )

    for col in feature_cat_cols:
        train_non_null = work_df.loc[train_idx, col].dropna()
        if not train_non_null.empty and work_df[col].isna().any():
            mode_val = train_non_null.mode().iloc[0]
            work_df[col] = work_df[col].fillna(mode_val)
            steps_applied.append(f"Fit mode imputer on Train for '{col}' (mode='{mode_val}').")

    if config.scaler_method != "none" and feature_numeric_cols:
        scaler_map = {
            "standard": StandardScaler(),
            "minmax": MinMaxScaler(),
            "robust": RobustScaler(),
        }
        scaler = scaler_map[config.scaler_method]
        scaler.fit(work_df.loc[train_idx, feature_numeric_cols])
        work_df[feature_numeric_cols] = np.round(
            scaler.transform(work_df[feature_numeric_cols]), 6
        )
        steps_applied.append(
            f"Fit {config.scaler_method} scaler strictly on Train and transformed {feature_numeric_cols}."
        )

    if config.one_hot_encode_categoricals and feature_cat_cols:
        work_df = pd.get_dummies(work_df, columns=feature_cat_cols, drop_first=False, dtype=int)
        steps_applied.append(f"One-hot encoded categorical features: {feature_cat_cols}.")

    return work_df, len(train_idx), len(test_idx), preserved_ids, steps_applied
