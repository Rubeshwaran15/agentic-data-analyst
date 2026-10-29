import re
import numpy as np
import pandas as pd
from app.schemas.quality import (
    OutlierColumnSummary,
    QualityAnalysisResponse,
    QualityIssueItem,
)


def analyze_dataset_quality(
    df: pd.DataFrame, target_column: str | None = None
) -> QualityAnalysisResponse:
    """
    Quality Analysis Agent:
    Performs all deterministic data-quality and ML-readiness checks with speed optimizations.
    """
    row_count = int(len(df))
    col_count = int(len(df.columns))
    total_cells = row_count * col_count if row_count * col_count > 0 else 1

    issues: list[QualityIssueItem] = []
    outlier_summaries: list[OutlierColumnSummary] = []
    issue_counter = 1

    # 1. Missing Values Check
    missing_series = df.isna().sum()
    cols_with_missing = missing_series[missing_series > 0]
    if not cols_with_missing.empty:
        total_missing = int(cols_with_missing.sum())
        missing_pct = round((total_missing / total_cells) * 100, 2)
        affected_cols = list(cols_with_missing.index)
        severity = (
            "high"
            if missing_pct > 15.0 or any((cols_with_missing / max(row_count, 1)) > 0.4)
            else "medium"
        )
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="missing_values",
                severity=severity,
                is_confirmed=True,
                affected_columns=affected_cols,
                title="Missing Values Detected",
                description=f"Found {total_missing:,} missing cells ({missing_pct}% of dataset) across {len(affected_cols)} columns.",
                affected_count=total_missing,
                affected_percentage=missing_pct,
                suggested_operations=[
                    "impute_numeric_median",
                    "impute_numeric_mean",
                    "impute_categorical_mode",
                    "impute_constant",
                ],
                details={"missing_breakdown": {col: int(cnt) for col, cnt in cols_with_missing.items()}},
            )
        )
        issue_counter += 1

    # 2. Exact Duplicate Rows Check
    if row_count > 0:
        exact_dups = int(df.duplicated().sum())
        if exact_dups > 0:
            dup_pct = round((exact_dups / row_count) * 100, 2)
            issues.append(
                QualityIssueItem(
                    issue_id=f"ISSUE_{issue_counter:03d}",
                    category="duplicates",
                    severity="high" if dup_pct > 5.0 else "medium",
                    is_confirmed=True,
                    affected_columns=list(df.columns),
                    title="Exact Duplicate Rows",
                    description=f"Identified {exact_dups:,} identical duplicate rows ({dup_pct}% of total records).",
                    affected_count=exact_dups,
                    affected_percentage=dup_pct,
                    suggested_operations=["remove_exact_duplicates"],
                    details={"exact_duplicate_count": exact_dups},
                )
            )
            issue_counter += 1

    # 3. Possible Duplicate Business Records (Speed-optimized: skipped if rows > 25,000)
    non_id_cols = [
        c for c in df.columns
        if not bool(re.search(r"(?:^|_)(?:id|uuid|guid|key|code)(?:$|_\d+$)", c))
    ]
    fuzzy_dups_count = 0
    if row_count > 1 and len(non_id_cols) >= 2 and row_count <= 25000:
        norm_subset = df[non_id_cols].copy()
        for c in non_id_cols:
            if pd.api.types.is_object_dtype(norm_subset[c]) or pd.api.types.is_string_dtype(norm_subset[c]):
                norm_subset[c] = norm_subset[c].astype(str).str.strip().str.lower()
        exact_dups_count = int(df.duplicated().sum())
        fuzzy_dups_count = int(norm_subset.duplicated().sum()) - exact_dups_count
        if fuzzy_dups_count > 0:
            issues.append(
                QualityIssueItem(
                    issue_id=f"ISSUE_{issue_counter:03d}",
                    category="duplicates",
                    severity="medium",
                    is_confirmed=False,
                    affected_columns=non_id_cols,
                    title="Possible Duplicate Business Records",
                    description=f"Found {fuzzy_dups_count:,} records that match on business attributes after normalizing text case/whitespace or ignoring IDs.",
                    affected_count=fuzzy_dups_count,
                    affected_percentage=round((fuzzy_dups_count / row_count) * 100, 2),
                    suggested_operations=["normalize_text", "remove_exact_duplicates"],
                )
            )
            issue_counter += 1

    # 4. Duplicate Identifiers
    for col in df.columns:
        if bool(re.search(r"(?:^|_)(?:id|uuid|guid|key|code)(?:$|_)", col)):
            non_null = df[col].dropna()
            if len(non_null) > 0:
                dup_ids = int(non_null.duplicated().sum())
                if dup_ids > 0:
                    dup_id_pct = round((dup_ids / len(non_null)) * 100, 2)
                    issues.append(
                        QualityIssueItem(
                            issue_id=f"ISSUE_{issue_counter:03d}",
                            category="duplicates",
                            severity="critical",
                            is_confirmed=True,
                            affected_columns=[col],
                            title=f"Duplicate Identifiers in '{col}'",
                            description=f"Column '{col}' appears to be an identifier but contains {dup_ids:,} duplicate values.",
                            affected_count=dup_ids,
                            affected_percentage=dup_id_pct,
                            suggested_operations=["remove_exact_duplicates", "drop_columns"],
                            details={"column": col, "duplicate_id_count": dup_ids},
                        )
                    )
                    issue_counter += 1

    # 5. Empty Rows and Columns
    empty_rows = int(df.isna().all(axis=1).sum())
    if empty_rows > 0:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="structural",
                severity="medium",
                is_confirmed=True,
                affected_columns=list(df.columns),
                title="Completely Empty Rows",
                description=f"Found {empty_rows} rows that contain no data whatsoever.",
                affected_count=empty_rows,
                affected_percentage=round((empty_rows / row_count) * 100, 2),
                suggested_operations=["remove_empty_rows"],
            )
        )
        issue_counter += 1

    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="structural",
                severity="high",
                is_confirmed=True,
                affected_columns=empty_cols,
                title="Completely Empty Columns",
                description=f"Columns {empty_cols} contain 100% missing values.",
                affected_count=len(empty_cols),
                affected_percentage=round((len(empty_cols) / col_count) * 100, 2),
                suggested_operations=["drop_columns"],
            )
        )
        issue_counter += 1

    # 6. Constant and Near-Constant Columns
    const_cols: list[str] = []
    near_const_cols: list[str] = []
    for col in df.columns:
        series = df[col].dropna()
        if len(series) <= 1:
            continue
        nunique = series.nunique()
        if nunique == 1:
            const_cols.append(col)
        else:
            top_freq_pct = (series.value_counts().iloc[0] / len(series)) * 100
            if top_freq_pct >= 99.0:
                near_const_cols.append(col)

    if const_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="variance",
                severity="medium",
                is_confirmed=True,
                affected_columns=const_cols,
                title="Constant Columns (Zero Variance)",
                description=f"Columns {const_cols} have only 1 unique value across all records.",
                affected_count=len(const_cols),
                affected_percentage=round((len(const_cols) / col_count) * 100, 2),
                suggested_operations=["drop_columns"],
            )
        )
        issue_counter += 1

    if near_const_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="variance",
                severity="low",
                is_confirmed=False,
                affected_columns=near_const_cols,
                title="Near-Constant Columns",
                description=f"Columns {near_const_cols} have >=99% identical values.",
                affected_count=len(near_const_cols),
                affected_percentage=round((len(near_const_cols) / col_count) * 100, 2),
                suggested_operations=["drop_columns"],
            )
        )
        issue_counter += 1

    # 7. Numbers Stored as Strings, Text Inconsistencies, Mixed Date Formats & High Cardinality
    string_cols = [
        c for c in df.columns
        if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])
    ]
    string_numbers_cols: list[str] = []
    whitespace_or_case_cols: list[str] = []
    invalid_date_cols: list[str] = []
    high_cardinality_cols: list[str] = []

    for col in string_cols:
        non_null = df[col].dropna().astype(str)
        if len(non_null) == 0:
            continue

        cleaned_num_test = non_null.str.replace(r"[\$,\s%]", "", regex=True)
        numeric_convertible = pd.to_numeric(cleaned_num_test, errors="coerce")
        if numeric_convertible.notna().mean() >= 0.8 and non_null.nunique() >= 2:
            string_numbers_cols.append(col)
            continue

        is_date_named = bool(
            re.search(r"(?:^|_)(?:date|time|timestamp|dt|dob|join_date|order_date)(?:$|_)", col)
        )
        if is_date_named:
            parsed_dates = pd.to_datetime(non_null, errors="coerce", format="mixed")
            invalid_ratio = float(parsed_dates.isna().mean())
            has_slash = bool(non_null.str.contains("/").any())
            has_dash = bool(non_null.str.contains("-").any())
            if (0.0 < invalid_ratio < 0.5) or (has_slash and has_dash):
                invalid_date_cols.append(col)

        has_ws = bool(non_null.str.startswith(" ").any() or non_null.str.endswith(" ").any())
        stripped = non_null.str.strip()
        case_collision = stripped.str.lower().nunique() < stripped.nunique()
        if has_ws or case_collision:
            whitespace_or_case_cols.append(col)

        is_id_named = bool(re.search(r"(?:^|_)(?:id|uuid|guid|key|code|name)(?:$|_)", col))
        if not is_id_named and len(non_null) >= 20:
            uniq_cnt = non_null.nunique()
            if uniq_cnt > 25 and (uniq_cnt / len(non_null)) > 0.6:
                high_cardinality_cols.append(col)

    if string_numbers_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="data_type",
                severity="medium",
                is_confirmed=True,
                affected_columns=string_numbers_cols,
                title="Numeric Data Stored as Strings",
                description=f"Columns {string_numbers_cols} contain numeric values formatted as text with currency symbols or commas.",
                affected_count=len(string_numbers_cols),
                affected_percentage=round((len(string_numbers_cols) / col_count) * 100, 2),
                suggested_operations=["convert_to_numeric"],
            )
        )
        issue_counter += 1

    if whitespace_or_case_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="text_inconsistency",
                severity="low",
                is_confirmed=True,
                affected_columns=whitespace_or_case_cols,
                title="Inconsistent Text Capitalization or Whitespace",
                description=f"Columns {whitespace_or_case_cols} contain leading/trailing whitespace or inconsistent casing.",
                affected_count=len(whitespace_or_case_cols),
                affected_percentage=round((len(whitespace_or_case_cols) / col_count) * 100, 2),
                suggested_operations=["normalize_text"],
            )
        )
        issue_counter += 1

    if invalid_date_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="date_anomaly",
                severity="medium",
                is_confirmed=True,
                affected_columns=invalid_date_cols,
                title="Invalid Dates or Mixed Date Formats",
                description=f"Date columns {invalid_date_cols} contain unparseable date strings or mixed separators ('/' and '-').",
                affected_count=len(invalid_date_cols),
                affected_percentage=round((len(invalid_date_cols) / col_count) * 100, 2),
                suggested_operations=["convert_data_type"],
            )
        )
        issue_counter += 1

    if high_cardinality_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="cardinality",
                severity="medium",
                is_confirmed=False,
                affected_columns=high_cardinality_cols,
                title="High-Cardinality Categorical Columns",
                description=f"Columns {high_cardinality_cols} have high unique category counts that may cause one-hot encoding explosion.",
                affected_count=len(high_cardinality_cols),
                affected_percentage=round((len(high_cardinality_cols) / col_count) * 100, 2),
                suggested_operations=["drop_columns"],
            )
        )
        issue_counter += 1

    # 8. Numeric Outliers (Both 1.5x IQR and Modified Z-Score > 3.5)
    numeric_cols = [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
    ]
    outlier_cols_detected: dict[str, int] = {}
    total_outliers_count = 0

    for col in numeric_cols:
        if bool(re.search(r"(?:^|_)(?:id|uuid|guid|key|code)(?:$|_\d+$)", col)):
            continue
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) < 4:
            continue

        q25, median, q75 = np.percentile(series, [25, 50, 75])
        iqr = q75 - q25
        lower_fence = float(q25 - 1.5 * iqr)
        upper_fence = float(q75 + 1.5 * iqr)

        iqr_mask = (series < lower_fence) | (series > upper_fence) if iqr > 0 else pd.Series(False, index=series.index)
        iqr_cnt = int(iqr_mask.sum())

        mad = float(np.median(np.abs(series - median)))
        if mad > 0:
            mod_z = 0.6745 * np.abs(series - median) / mad
            mod_z_mask = mod_z > 3.5
            mod_z_cnt = int(mod_z_mask.sum())
        else:
            mod_z_mask = pd.Series(False, index=series.index)
            mod_z_cnt = 0

        combined_outliers = series[iqr_mask | mod_z_mask]
        combined_cnt = int(len(combined_outliers))

        outlier_summaries.append(
            OutlierColumnSummary(
                column=col,
                total_non_null=int(len(series)),
                iqr_outlier_count=iqr_cnt,
                mod_z_outlier_count=mod_z_cnt,
                outlier_percentage=round((combined_cnt / len(series)) * 100, 2),
                min_val=round(float(series.min()), 4),
                q25=round(float(q25), 4),
                median=round(float(median), 4),
                q75=round(float(q75), 4),
                max_val=round(float(series.max()), 4),
                lower_fence=round(lower_fence, 4),
                upper_fence=round(upper_fence, 4),
                sample_outliers=[round(float(x), 4) for x in combined_outliers.head(8)],
            )
        )

        if combined_cnt > 0:
            outlier_cols_detected[col] = combined_cnt
            total_outliers_count += combined_cnt

    if outlier_cols_detected:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="outliers",
                severity="medium",
                is_confirmed=False,
                affected_columns=list(outlier_cols_detected.keys()),
                title="Numeric Outliers Detected (IQR & Modified Z-Score)",
                description=f"Found {total_outliers_count:,} potential outlier values across {len(outlier_cols_detected)} numeric column(s) via 1.5x IQR and Modified Z-Score.",
                affected_count=total_outliers_count,
                affected_percentage=round((total_outliers_count / max(row_count * len(numeric_cols), 1)) * 100, 2),
                suggested_operations=["cap_outliers", "detect_outliers", "remove_outliers"],
                details={"outlier_counts": outlier_cols_detected},
            )
        )
        issue_counter += 1

    # 9. Skewed Distributions
    skewed_cols: list[tuple[str, float]] = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) >= 6:
            skew_val = float(series.skew())
            if abs(skew_val) > 1.5:
                skewed_cols.append((col, round(skew_val, 2)))

    if skewed_cols:
        issues.append(
            QualityIssueItem(
                issue_id=f"ISSUE_{issue_counter:03d}",
                category="distribution",
                severity="low",
                is_confirmed=False,
                affected_columns=[c[0] for c in skewed_cols],
                title="Highly Skewed Numeric Distributions",
                description=f"Columns {[c[0] for c in skewed_cols]} exhibit strong skewness (|skew| > 1.5).",
                affected_count=len(skewed_cols),
                affected_percentage=round((len(skewed_cols) / max(len(numeric_cols), 1)) * 100, 2),
                suggested_operations=["apply_scaler", "cap_outliers"],
                details={"skewness_values": dict(skewed_cols)},
            )
        )
        issue_counter += 1

    # 10. Highly Correlated Numeric Columns (Speed-optimized: capped at 30 columns max)
    if len(numeric_cols) > 30:
        numeric_cols = numeric_cols[:30]

    if len(numeric_cols) >= 2 and row_count >= 5:
        corr_matrix = df[numeric_cols].corr().abs()
        high_corr_pairs: list[str] = []
        correlated_col_set: set[str] = set()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                c1, c2 = numeric_cols[i], numeric_cols[j]
                r_val = corr_matrix.loc[c1, c2]
                if pd.notna(r_val) and float(r_val) > 0.85:
                    high_corr_pairs.append(f"{c1} ↔ {c2} (r={round(float(r_val), 3)})")
                    correlated_col_set.update([c1, c2])

        if high_corr_pairs:
            issues.append(
                QualityIssueItem(
                    issue_id=f"ISSUE_{issue_counter:03d}",
                    category="correlation",
                    severity="medium",
                    is_confirmed=False,
                    affected_columns=sorted(correlated_col_set),
                    title="Highly Correlated Numeric Features (Multicollinearity)",
                    description=f"Detected {len(high_corr_pairs)} strongly correlated feature pair(s): {', '.join(high_corr_pairs)}.",
                    affected_count=len(high_corr_pairs),
                    affected_percentage=round((len(correlated_col_set) / col_count) * 100, 2),
                    suggested_operations=["drop_columns"],
                    details={"correlated_pairs": high_corr_pairs},
                )
            )
            issue_counter += 1

    # 11. Target Class Imbalance & Potential Data Leakage
    if target_column and target_column in df.columns:
        target_series = df[target_column].dropna()
        if 2 <= target_series.nunique() <= 20 and len(target_series) >= 5:
            val_Receive = target_series.value_counts(normalize=True)
            majority_pct = round(float(val_Receive.iloc[0]) * 100, 2)
            minority_pct = round(float(val_Receive.iloc[-1]) * 100, 2)
            if majority_pct >= 75.0 or minority_pct < 15.0:
                issues.append(
                    QualityIssueItem(
                        issue_id=f"ISSUE_{issue_counter:03d}",
                        category="ml_readiness",
                        severity="high" if majority_pct >= 85.0 else "medium",
                        is_confirmed=True,
                        affected_columns=[target_column],
                        title=f"Target Class Imbalance in '{target_column}'",
                        description=f"Majority class represents {majority_pct}% while minority class is {minority_pct}%. Consider stratified splitting or class weights.",
                        affected_count=int(target_series.value_counts().iloc[-1]),
                        affected_percentage=minority_pct,
                        suggested_operations=[],
                        details={"majority_pct": majority_pct, "minority_pct": minority_pct},
                    )
                )
                issue_counter += 1

        leakage_suspects: list[str] = []
        if pd.api.types.is_numeric_dtype(df[target_column]):
            target_num = pd.to_numeric(df[target_column], errors="coerce")
        else:
            target_num = pd.Series(pd.factorize(df[target_column])[0], index=df.index, dtype=float)

        for col in df.columns:
            if col == target_column:
                continue
            if pd.api.types.is_numeric_dtype(df[col]) and len(df) >= 5:
                r_leak = target_num.corr(pd.to_numeric(df[col], errors="coerce"))
                if pd.notna(r_leak) and abs(float(r_leak)) >= 0.97:
                    leakage_suspects.append(f"{col} (|r|={round(abs(float(r_leak)), 3)})")

        if leakage_suspects:
            issues.append(
                QualityIssueItem(
                    issue_id=f"ISSUE_{issue_counter:03d}",
                    category="ml_readiness",
                    severity="critical",
                    is_confirmed=False,
                    affected_columns=[s.split(" ")[0] for s in leakage_suspects],
                    title="Potential Target Data Leakage Detected",
                    description=f"Feature(s) {', '.join(leakage_suspects)} exhibit near-perfect correlation (>=0.97) with target '{target_column}'. Verify they are not post-event leakage.",
                    affected_count=len(leakage_suspects),
                    affected_percentage=round((len(leakage_suspects) / col_count) * 100, 2),
                    suggested_operations=["drop_columns"],
                    details={"leakage_suspects": leakage_suspects},
                )
            )
            issue_counter += 1

    confirmed_count = sum(1 for i in issues if i.is_confirmed)
    potential_count = sum(1 for i in issues if not i.is_confirmed)

    risk_score = min(
        100,
        int(
            sum(
                5 if i.severity == "low" else 15 if i.severity == "medium" else 25 if i.severity == "high" else 35
                for i in issues
            )
        ),
    )

    return QualityAnalysisResponse(
        dataset_id="",
        target_column=target_column,
        total_issues_found=len(issues),
        confirmed_issues_count=confirmed_count,
        potential_anomalies_count=potential_count,
        risk_score=risk_score,
        issues=issues,
        outlier_summaries=outlier_summaries,
    )