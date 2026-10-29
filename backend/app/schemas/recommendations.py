from typing import Any, Literal
from pydantic import BaseModel, Field

OperationType = Literal[
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

RiskLevel = Literal["low", "medium", "high"]


class PreprocessingRecommendationItem(BaseModel):
    operation: OperationType
    columns: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    reason: str
    risk: RiskLevel
    requires_approval: bool = True


class AIPreprocessingPlan(BaseModel):
    summary: str
    recommendations: list[PreprocessingRecommendationItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_by: Literal["ollama_qwen2.5:1.5b", "deterministic_fallback"] = "deterministic_fallback"