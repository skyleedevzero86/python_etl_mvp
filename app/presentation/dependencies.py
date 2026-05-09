from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.application.dashboard_service import DashboardApplicationService
from app.application.pipeline_service import PipelineApplicationService
from app.infrastructure.repositories.dashboard_mysql import MysqlDashboardRepository
from app.infrastructure.repositories.pipeline_mysql import MysqlPipelineRepository


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_db(
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_pipeline_service(
    session: Annotated[Session, Depends(get_db)],
) -> PipelineApplicationService:
    return PipelineApplicationService(MysqlPipelineRepository(session))


def get_dashboard_service(
    session: Annotated[Session, Depends(get_db)],
) -> DashboardApplicationService:
    return DashboardApplicationService(MysqlDashboardRepository(session))
