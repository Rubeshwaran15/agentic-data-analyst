from typing import Any
from pydantic import BaseModel, Field


class ColumnMappingItem(BaseModel):
    index: int
    original_name: str
    standardized_name: str
    was_modified: bool
    modification_notes: list[str] = Field(default_factory=list)


class ColumnStandardizationReport(BaseModel):
    total_columns: int
    modified_count: int
    duplicate_names_resolved: int
    empty_names_filled: int
    mappings: list[ColumnMappingItem]
    original_to_standardized: dict[str, str]


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    filename: str
    file_format: str
    row_count: int
    column_count: int
    columns: list[str]
    preview_rows: list[dict[str, Any]]


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_format: str
    file_size_bytes: int
    row_count: int
    column_count: int
    standardization_report: ColumnStandardizationReport
    preview: DatasetPreviewResponse