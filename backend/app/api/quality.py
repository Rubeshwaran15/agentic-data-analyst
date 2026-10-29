from fastapi import APIRouter, Query
from app.schemas.quality import QualityAnalysisResponse
from app.services.quality_analyzer import analyze_dataset_quality
from app.services.session_store import session_store

router = APIRouter(prefix="/api/quality", tags=["Quality Analysis"])


@router.get("/{dataset_id}", response_model=QualityAnalysisResponse)
async def get_dataset_quality(
    dataset_id: str,
    target_column: str | None = Query(default=None, description="Optional ML target column for imbalance and leakage analysis"),
) -> QualityAnalysisResponse:
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)
    quality_response = analyze_dataset_quality(df, target_column=target_column)
    quality_response.dataset_id = session.dataset_id
    return quality_response