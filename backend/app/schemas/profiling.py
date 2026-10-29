from typing import Any, Literal
from pydantic import BaseModel, Field

SemanticColumnType = Literal[
    "numeric",
    "categorical",
    "boolean",
    "datetime",
    "identifier",
    "text",
]


class NumericStats(BaseModel):
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    q25: float | None = None
    median: float | None = None
    q75: float | None = None
    max: float | None = None
    skewness: float | None = None
    zeros_count: int = 0
    negative_count: int = 0


class FrequentValueItem(BaseModel):
    value: str
    count: int
    percentage: float


class ColumnProfile(BaseModel):
    name: str
    original_name: str
    pandas_dtype: str
    semantic_type: SemanticColumnType
    total_count: int
    null_count: int
    null_percentage: float
    non_null_count: int
    unique_count: int
    unique_percentage: float
    memory_bytes: int
    sample_values: list[Any] = Field(default_factory=list)
    numeric_stats: NumericStats | None = None
    top_values: list[FrequentValueItem] = Field(default_factory=list)


class DatasetProfileResponse(BaseModel):
    dataset_id: str
    filename: str
    row_count: int
    column_count: int
    memory_usage_bytes: int
    memory_usage_human: str
    total_missing_cells: int
    total_missing_percentage: float
    exact_duplicate_rows: int
    exact_duplicate_percentage: float
    semantic_type_counts: dict[str, int]
    column_profiles: list[ColumnProfile]