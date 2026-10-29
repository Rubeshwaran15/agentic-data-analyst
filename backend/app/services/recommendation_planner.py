import json
import logging
from app.schemas.quality import QualityAnalysisResponse
from app.schemas.recommendations import (
    AIPreprocessingPlan,
    PreprocessingRecommendationItem,
)
from app.services.ollama_client import query_ollama_chat

logger = logging.getLogger(__name__)


def generate_deterministic_fallback_plan(
    quality_response: QualityAnalysisResponse,
    valid_columns: list[str],
    user_goal: str | None = None,
) -> AIPreprocessingPlan:
    """
    Generates a deterministic preprocessing plan when Ollama is offline or unreachable.
    """
    recommendations: list[PreprocessingRecommendationItem] = []
    warnings: list[str] = []

    for issue in quality_response.issues:
        cols = [c for c in issue.affected_columns if c in valid_columns]
        if issue.category == "duplicates" and "remove_exact_duplicates" in issue.suggested_operations:
            if not any(r.operation == "remove_exact_duplicates" for r in recommendations):
                recommendations.append(
                    PreprocessingRecommendationItem(
                        operation="remove_exact_duplicates",
                        columns=[],
                        parameters={},
                        reason="Remove exact duplicate rows to prevent biased statistics and training leakage.",
                        risk="low",
                        requires_approval=True,
                    )
                )
        elif issue.category == "data_type" and cols:
            recommendations.append(
                PreprocessingRecommendationItem(
                    operation="convert_to_numeric",
                    columns=cols,
                    parameters={},
                    reason=f"Convert currency/string-formatted numbers in {cols} into clean numeric types.",
                    risk="low",
                    requires_approval=True,
                )
            )
        elif issue.category == "text_inconsistency" and cols:
            recommendations.append(
                PreprocessingRecommendationItem(
                    operation="normalize_text",
                    columns=cols,
                    parameters={"trim_whitespace": True, "normalize_case": True},
                    reason=f"Trim leading/trailing whitespace and standardize casing in {cols}.",
                    risk="low",
                    requires_approval=True,
                )
            )
        elif issue.category == "missing_values" and cols:
            recommendations.append(
                PreprocessingRecommendationItem(
                    operation="impute_numeric_median",
                    columns=cols,
                    parameters={},
                    reason="Impute missing values after verifying numeric/categorical column types.",
                    risk="low",
                    requires_approval=True,
                )
            )
        elif issue.category == "variance" and issue.is_confirmed and cols:
            recommendations.append(
                PreprocessingRecommendationItem(
                    operation="drop_columns",
                    columns=cols,
                    parameters={},
                    reason=f"Drop zero-variance constant column(s) {cols} as they carry no predictive signal.",
                    risk="medium",
                    requires_approval=True,
                )
            )
        elif issue.category == "outliers" and cols:
            recommendations.append(
                PreprocessingRecommendationItem(
                    operation="cap_outliers",
                    columns=cols,
                    parameters={"iqr_multiplier": 1.5},
                    reason=f"Cap extreme outlier values in {cols} using 1.5x IQR bounds rather than deleting rows.",
                    risk="medium",
                    requires_approval=True,
                )
            )

    warnings.append("Review extreme values in the Outlier Visualizer before approving capping or removal.")
    if quality_response.target_column:
        warnings.append(
            f"Target column '{quality_response.target_column}' selected: use the ML-Ready Pipeline Studio to fit transformations strictly on the training split."
        )

    goal_prefix = f"Goal: '{user_goal}'. " if user_goal else ""
    return AIPreprocessingPlan(
        summary=f"{goal_prefix}Deterministic analyzer detected {quality_response.total_issues_found} quality findings (Risk Score: {quality_response.risk_score}/100) and prepared {len(recommendations)} safe recommendations.",
        recommendations=recommendations,
        warnings=warnings,
        generated_by="deterministic_fallback",
    )


async def generate_ai_recommendation_plan(
    quality_response: QualityAnalysisResponse,
    valid_columns: list[str],
    user_goal: str | None = None,
) -> AIPreprocessingPlan:
    """
    AI Planning Agent:
    Sends compact quality digest + user's preprocessing goal to Qwen2.5 1.5B via Ollama.
    Includes a self-correction retry if initial JSON or column references fail validation.
    """
    allowed_ops = [
        "standardize_column_names",
        "remove_exact_duplicates",
        "remove_empty_rows",
        "drop_columns",
        "impute_numeric_mean",
        "impute_numeric_median",
        "impute_constant",
        "impute_categorical_mode",
        "normalize_text",
        "convert_to_numeric",
        "convert_data_type",
        "detect_outliers",
        "cap_outliers",
        "remove_outliers",
        "one_hot_encode",
        "ordinal_encode",
        "apply_scaler",
    ]

    system_prompt = (
        "You are a Senior Agentic Data Preprocessing & Quality Analyst AI. "
        "Review the deterministic data-quality findings and user goal, then output ONLY valid JSON matching this exact schema:\n"
        "{\n"
        '  "summary": "Concise executive explanation",\n'
        '  "recommendations": [\n'
        "    {\n"
        f'      "operation": one of {allowed_ops},\n'
        '      "columns": ["existing_column_name"],\n'
        '      "parameters": {},\n'
        '      "reason": "Why this transformation helps",\n'
        '      "risk": "low" | "medium" | "high",\n'
        '      "requires_approval": true\n'
        "    }\n"
        "  ],\n"
        '  "warnings": ["Important caution for the data analyst"]\n'
        "}\n"
        f"CRITICAL RULES: Only use columns from this exact list: {valid_columns}. "
        "Never invent column names or unsupported operations."
    )

    compact_digest = {
        "user_goal": user_goal or "General data cleaning and ML readiness",
        "target_column": quality_response.target_column,
        "risk_score": quality_response.risk_score,
        "available_columns": valid_columns,
        "issues": [
            {
                "category": i.category,
                "severity": i.severity,
                "is_confirmed": i.is_confirmed,
                "affected_columns": i.affected_columns,
                "title": i.title,
                "suggested_operations": i.suggested_operations,
            }
            for i in quality_response.issues
        ],
    }

    user_prompt = f"Generate a structured preprocessing plan for this dataset digest:\n{json.dumps(compact_digest, indent=2)}"

    for attempt in range(2):
        try:
            raw_json_str = await query_ollama_chat(system_prompt, user_prompt)
            parsed_data = json.loads(raw_json_str)
            plan = AIPreprocessingPlan(**parsed_data)

            # Verify every referenced column exists
            valid_set = set(valid_columns)
            for rec in plan.recommendations:
                invalid_cols = [c for c in rec.columns if c not in valid_set]
                if invalid_cols:
                    raise ValueError(f"Model referenced nonexistent columns: {invalid_cols}")

            plan.generated_by = "ollama_qwen2.5:1.5b"
            return plan
        except Exception as exc:
            logger.warning(f"Ollama attempt {attempt + 1} validation issue: {exc}")
            user_prompt = (
                f"Your previous response failed validation with error: {exc}. "
                f"Correct the JSON so it strictly uses allowed operations {allowed_ops} "
                f"and valid columns {valid_columns}."
            )

    return generate_deterministic_fallback_plan(quality_response, valid_columns, user_goal=user_goal)