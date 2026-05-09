from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.application.dashboard_service import DashboardApplicationService
from app.domain.dashboard_schema import DashboardSnapshot, TableDetailSnapshot, TableStatsSnapshot
from app.presentation.dependencies import get_dashboard_service

router = APIRouter(tags=["대시보드"])

_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES))


@router.get("/", include_in_schema=False)
def dashboard_root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    summary="대시보드 화면",
    description="대시보드 HTML 페이지를 반환합니다. 실제 수치 데이터는 `/api/dashboard/stats`에서 가져옵니다.",
)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )


@router.get(
    "/api/dashboard/stats",
    response_model=DashboardSnapshot,
    summary="대시보드 집계 JSON",
    description="게이지, 월별 추이, 진료유형 비중, 상위 진료과, KPI를 한 번에 반환합니다.",
)
def dashboard_stats_json(
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> DashboardSnapshot:
    return service.get_snapshot()


@router.get(
    "/api/dashboard/table-stats",
    response_model=TableStatsSnapshot,
    summary="테이블별 통계 목록",
    description="주요 테이블별 전체 건수, 오늘 생성 건수, 마지막 생성 시각을 반환합니다.",
)
def dashboard_table_stats_json(
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> TableStatsSnapshot:
    return service.get_table_stats()


@router.get(
    "/api/dashboard/table-stats/{table_name}",
    response_model=TableDetailSnapshot,
    summary="테이블 통계 상세",
    description="단일 테이블의 기본 지표, 최근 14일 생성 추이, 최근 20개 레코드를 반환합니다.",
    responses={404: {"description": "알 수 없는 테이블 이름"}},
)
def dashboard_table_detail_json(
    table_name: Annotated[
        str,
        Path(
            description="조회할 테이블명",
            examples=["treatments", "Patient", "examination_schedule"],
        ),
    ],
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> TableDetailSnapshot:
    try:
        return service.get_table_detail(table_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/dashboard/tables",
    response_class=HTMLResponse,
    summary="테이블 통계 페이지",
    description="테이블별 건수를 표 형태로 보여주는 HTML 페이지입니다.",
)
def dashboard_tables_page(
    request: Request,
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> HTMLResponse:
    stats = service.get_table_stats()
    return templates.TemplateResponse(
        request=request,
        name="dashboard_tables.html",
        context={"stats": stats},
    )


@router.get(
    "/dashboard/tables/{table_name}",
    response_class=HTMLResponse,
    summary="테이블 통계 상세 페이지",
    description="선택한 테이블의 지표와 최근 레코드를 보여주는 HTML 페이지입니다.",
    responses={404: {"description": "알 수 없는 테이블 이름"}},
)
def dashboard_table_detail_page(
    table_name: Annotated[
        str,
        Path(
            description="조회할 테이블명",
            examples=["treatments", "Patient", "examination_schedule"],
        ),
    ],
    request: Request,
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> HTMLResponse:
    try:
        detail = service.get_table_detail(table_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return templates.TemplateResponse(
        request=request,
        name="dashboard_table_detail.html",
        context={"detail": detail},
    )
