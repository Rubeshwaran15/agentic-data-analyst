from fastapi import APIRouter
from app.schemas.profiling import DatasetProfileResponse
from app.services.profiler import profile_dataset
from app.services.session_store import session_store

router = APIRouter(prefix="/api/profiling", tags=["Profiling"])


@router.get("/{dataset_id}", response_model=DatasetProfileResponse)
async def get_dataset_profile(dataset_id: str) -> DatasetProfileResponse:
    session = session_store.get_session(dataset_id)
    df = session_store.load_dataframe(dataset_id)
    return profile_dataset(df, session)