from fastapi import APIRouter, File, UploadFile
from app.schemas.dataset import (
    ColumnStandardizationReport,
    DatasetPreviewResponse,
    DatasetUploadResponse,
)
from app.services.column_normalizer import standardize_column_names
from app.services.dataset_loader import parse_tabular_bytes, validate_file_metadata
from app.services.profiler import build_dataset_preview
from app.services.session_store import session_store

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetUploadResponse:
    raw_bytes = await file.read()
    filename = file.filename or "uploaded_dataset.csv"

    extension = validate_file_metadata(filename=filename, file_size_bytes=len(raw_bytes))
    raw_df = parse_tabular_bytes(raw_bytes=raw_bytes, extension=extension)

    standardized_df, standardization_report = standardize_column_names(raw_df)

    session = session_store.create_session(
        filename=filename,
        file_format=extension,
        raw_bytes=raw_bytes,
        standardized_df=standardized_df,
        standardization_report=standardization_report,
    )

    preview = build_dataset_preview(standardized_df, session)

    return DatasetUploadResponse(
        dataset_id=session.dataset_id,
        filename=session.filename,
        file_format=session.file_format,
        file_size_bytes=session.file_size_bytes,
        row_count=len(standardized_df),
        column_count=len(standardized_df.columns),
        standardization_report=standardization_report,
        preview=preview,
    )


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def get_dataset_preview(dataset_id: str) -> DatasetPreviewResponse:
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)
    return build_dataset_preview(df, session)


@router.get("/{dataset_id}/column-mapping", response_model=ColumnStandardizationReport)
async def get_column_mapping(dataset_id: str) -> ColumnStandardizationReport:
    session = session_store.get_session(dataset_id)
    return session.standardization_report