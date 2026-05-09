from fastapi import APIRouter, Response

from app.domain.api_schema import HealthResponse

router = APIRouter(tags=["상태점검"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="헬스 체크",
    description="애플리케이션 프로세스의 기본 동작 상태를 반환합니다.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
def chrome_devtools_probe() -> Response:
    return Response(status_code=204)
