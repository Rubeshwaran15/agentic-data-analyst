from typing import Any, Literal
from pydantic import BaseModel, Field
from app.schemas.recommendations import OperationType


class TransformationRequest(BaseModel):
    operation: OperationType
    columns: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    approved_by_user: bool = False
    use_ml_train_test_split: bool = False
    train_size: float = Field(default=0.8, ge=0.5, le=0.95)


class ValidationCheckItem(BaseModel):
    check_name: str
    passed: bool
    details: str


class ValidationReport(BaseModel):
    is_valid: bool
    checks: list[ValidationCheckItem] = Field(default_factory=list)


class TransformationEffectSummary(BaseModel):
    operation: OperationType
    target_columns: list[str]
    rows_before: int
    rows_after: int
    rows_delta: int
    cols_before: int
    cols_after: int
    cols_delta: int
    missing_before: int
    missing_after: int
    missing_delta: int
    execution_notes: list[str] = Field(default_factory=list)
    sample_before: list[dict[str, Any]] = Field(default_factory=list)
    sample_after: list[dict[str, Any]] = Field(default_factory=list)


class TransformationExecutionResponse(BaseModel):
    dataset_id: str
    snapshot_version: int
    status: str
    message: str
    effect: TransformationEffectSummary
    validation: ValidationReport


class AuditLogEntrySchema(BaseModel):
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


class AuditHistoryResponse(BaseModel):
    dataset_id: str
    current_version: int
    total_versions: int
    can_undo: bool
    entries: list[AuditLogEntrySchema]


class BeforeAfterComparisonResponse(BaseModel):
    dataset_id: str
    baseline_version: int
    current_version: int
    rows_baseline: int
    rows_current: int
    rows_delta: int
    cols_baseline: int
    cols_current: int
    cols_delta: int
    missing_baseline: int
    missing_current: int
    missing_delta: int
    duplicates_baseline: int
    duplicates_current: int
    duplicates_delta: int
    risk_score_baseline: int
    risk_score_current: int
    risk_score_delta: int
    added_columns: list[str]
    removed_columns: list[str]
    baseline_sample: list[dict[str, Any]]
    current_sample: list[dict[str, Any]]


class MLPipelineRequest(BaseModel):
    target_column: str | None = None
    train_size: float = Field(default=0.8, ge=0.5, le=0.95)
    numeric_impute_strategy: Literal["median", "mean"] = "median"
    scaler_method: Literal["standard", "minmax", "robust", "none"] = "standard"
    one_hot_encode_categoricals: bool = True
    drop_constant_columns: bool = True
    approved_by_user: bool = False


class MLPipelineExecutionResponse(BaseModel):
    dataset_id: str
    snapshot_version: int
    train_rows: int
    test_rows: int
    features_before: int
    features_after: int
    preserved_identifiers: list[str]
    target_column: str | None
    steps_applied: list[str]
    validation: ValidationReport
