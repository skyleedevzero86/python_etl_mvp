from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
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


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={},
    )


@router.get("/api/dashboard/stats", response_model=DashboardSnapshot)
def dashboard_stats_json(
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> DashboardSnapshot:
    return service.get_snapshot()


@router.get("/api/dashboard/table-stats", response_model=TableStatsSnapshot)
def dashboard_table_stats_json(
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> TableStatsSnapshot:
    return service.get_table_stats()


@router.get("/api/dashboard/table-stats/{table_name}", response_model=TableDetailSnapshot)
def dashboard_table_detail_json(
    table_name: str,
    service: Annotated[DashboardApplicationService, Depends(get_dashboard_service)],
) -> TableDetailSnapshot:
    try:
        return service.get_table_detail(table_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard/tables", response_class=HTMLResponse)
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


@router.get("/dashboard/tables/{table_name}", response_class=HTMLResponse)
def dashboard_table_detail_page(
    table_name: str,
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
