from typing import Any, Literal
from pydantic import BaseModel, Field

IssueSeverity = Literal["low", "medium", "high", "critical"]
IssueCategory = Literal[
    "missing_values",
    "duplicates",
    "outliers",
    "data_type",
    "text_inconsistency",
    "date_anomaly",
    "structural",
    "variance",
    "cardinality",
    "distribution",
    "correlation",
    "ml_readiness",
]


class OutlierColumnSummary(BaseModel):
    column: str
    total_non_null: int
    iqr_outlier_count: int
    mod_z_outlier_count: int
    outlier_percentage: float
    min_val: float
    q25: float
    median: float
    q75: float
    max_val: float
    lower_fence: float
    upper_fence: float
    sample_outliers: list[float] = Field(default_factory=list)


class QualityIssueItem(BaseModel):
    issue_id: str
    category: IssueCategory
    severity: IssueSeverity
    is_confirmed: bool
    affected_columns: list[str] = Field(default_factory=list)
    title: str
    description: str
    affected_count: int
    affected_percentage: float
    suggested_operations: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class QualityAnalysisResponse(BaseModel):
    dataset_id: str
    target_column: str | None = None
    total_issues_found: int
    confirmed_issues_count: int
    potential_anomalies_count: int
    risk_score: int
    issues: list[QualityIssueItem] = Field(default_factory=list)
    outlier_summaries: list[OutlierColumnSummary] = Field(default_factory=list)
