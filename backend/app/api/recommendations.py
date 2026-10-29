from fastapi import APIRouter
from app.schemas.recommendations import AIPreprocessingPlan
from app.services.quality_analyzer import analyze_dataset_quality
from app.services.recommendation_planner import generate_ai_recommendation_plan
from app.services.session_store import session_store

router = APIRouter(prefix="/api/recommendations", tags=["AI Recommendations"])


@router.get("/{dataset_id}", response_model=AIPreprocessingPlan)
async def get_dataset_recommendations(dataset_id: str) -> AIPreprocessingPlan:
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)
    quality_response = analyze_dataset_quality(df)
    valid_columns = list(df.columns)

    plan = await generate_ai_recommendation_plan(quality_response, valid_columns)
    return plan