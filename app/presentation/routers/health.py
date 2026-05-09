from fastapi import APIRouter

from app.domain.api_schema import HealthResponse

router = APIRouter(tags=["상태점검"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
