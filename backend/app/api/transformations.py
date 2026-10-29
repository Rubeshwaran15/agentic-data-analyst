from fastapi import APIRouter
from app.core.exceptions import DatasetError
from app.schemas.transformations import (
    AuditHistoryResponse,
    BeforeAfterComparisonResponse,
    MLPipelineExecutionResponse,
    MLPipelineRequest,
    TransformationEffectSummary,
    TransformationExecutionResponse,
    TransformationRequest,
)
from app.services.audit_logger import (
    build_before_after_comparison,
    get_audit_history,
)
from app.services.session_store import session_store
from app.services.transformation_engine import (
    execute_leak_free_ml_pipeline,
    preview_transformation_effect,
)
from app.services.validation_engine import validate_transformation_result

router = APIRouter(prefix="/api/transformations", tags=["Safe Transformations & Audit History"])


@router.post("/{dataset_id}/preview", response_model=TransformationEffectSummary)
async def preview_transformation(
    dataset_id: str, request: TransformationRequest
) -> TransformationEffectSummary:
    df = session_store.load_dataframe(dataset_id)
    _, effect = preview_transformation_effect(df, request)
    return effect


@router.post("/{dataset_id}/execute", response_model=TransformationExecutionResponse)
async def execute_transformation(
    dataset_id: str, request: TransformationRequest
) -> TransformationExecutionResponse:
    if not request.approved_by_user:
        raise DatasetError(
            "User approval is required before executing any preprocessing operation.",
            status_code=400,
        )

    df = session_store.load_dataframe(dataset_id)
    transformed_df, effect = preview_transformation_effect(df, request)

    validation_report = validate_transformation_result(df, transformed_df, request)

    version = session_store.save_new_snapshot(
        dataset_id=dataset_id,
        new_df=transformed_df,
        operation=request.operation,
        columns=request.columns,
        parameters=request.parameters,
        rows_before=effect.rows_before,
        cols_before=effect.cols_before,
        missing_before=effect.missing_before,
        missing_after=effect.missing_after,
        validation_passed=validation_report.is_valid,
        notes=effect.execution_notes,
    )

    return TransformationExecutionResponse(
        dataset_id=dataset_id,
        snapshot_version=version,
        status="completed",
        message="; ".join(effect.execution_notes) or f"Executed {request.operation} successfully.",
        effect=effect,
        validation=validation_report,
    )


@router.post("/{dataset_id}/ml-pipeline", response_model=MLPipelineExecutionResponse)
async def run_ml_pipeline(
    dataset_id: str, request: MLPipelineRequest
) -> MLPipelineExecutionResponse:
    if not request.approved_by_user:
        raise DatasetError(
            "Explicit user approval is required before running the ML pipeline.",
            status_code=400,
        )

    df = session_store.load_dataframe(dataset_id)
    rows_before = int(len(df))
    cols_before = int(len(df.columns))
    missing_before = int(df.isna().sum().sum())

    ml_df, train_rows, test_rows, preserved_ids, steps = execute_leak_free_ml_pipeline(
        df, request
    )

    dummy_req = TransformationRequest(
        operation="apply_scaler",
        columns=[],
        approved_by_user=True,
    )
    validation_report = validate_transformation_result(df, ml_df, dummy_req)

    version = session_store.save_new_snapshot(
        dataset_id=dataset_id,
        new_df=ml_df,
        operation="ml_ready_train_test_pipeline",
        columns=list(ml_df.columns),
        parameters=request.model_dump(),
        rows_before=rows_before,
        cols_before=cols_before,
        missing_before=missing_before,
        missing_after=int(ml_df.isna().sum().sum()),
        validation_passed=validation_report.is_valid,
        notes=steps,
    )

    return MLPipelineExecutionResponse(
        dataset_id=dataset_id,
        snapshot_version=version,
        train_rows=train_rows,
        test_rows=test_rows,
        features_before=cols_before,
        features_after=int(len(ml_df.columns)),
        preserved_identifiers=preserved_ids,
        target_column=request.target_column,
        steps_applied=steps,
        validation=validation_report,
    )


@router.get("/{dataset_id}/history", response_model=AuditHistoryResponse)
async def fetch_history(dataset_id: str) -> AuditHistoryResponse:
    return get_audit_history(dataset_id)


@router.post("/{dataset_id}/undo", response_model=AuditHistoryResponse)
async def undo_transformation(dataset_id: str) -> AuditHistoryResponse:
    session_store.undo_last_snapshot(dataset_id)
    return get_audit_history(dataset_id)


@router.post("/{dataset_id}/restore/{version}", response_model=AuditHistoryResponse)
async def restore_version(dataset_id: str, version: int) -> AuditHistoryResponse:
    session_store.restore_snapshot_version(dataset_id, version)
    return get_audit_history(dataset_id)


@router.get("/{dataset_id}/comparison", response_model=BeforeAfterComparisonResponse)
async def fetch_comparison(dataset_id: str) -> BeforeAfterComparisonResponse:
    return build_before_after_comparison(dataset_id)