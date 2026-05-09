import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.pipeline_service import PipelineApplicationService
from app.domain.enums import PipelineJob
from app.infrastructure.config import Settings
from app.infrastructure.etl_scheduler import register_etl_jobs
from app.infrastructure.repositories.pipeline_mysql import MysqlPipelineRepository

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)


def _run_job(factory: "sessionmaker[Session]", job: PipelineJob, daily_rows: int) -> None:
    session = factory()
    try:
        repo = MysqlPipelineRepository(session, daily_rows=daily_rows)
        svc = PipelineApplicationService(repo)
        result = svc.execute(job)
        session.commit()
        logger.info("파이프라인 작업 정상 종료, 유형=%s, 결과=%s", job.value, result)
    except Exception:
        session.rollback()
        logger.exception("파이프라인 작업 실패, 유형=%s", job.value)
        raise
    finally:
        session.close()


def start_background_scheduler(
    settings: Settings,
    session_factory: "sessionmaker[Session]",
    postgres_engine: "Engine | None" = None,
) -> BackgroundScheduler | None:

    pipeline_on = settings.enable_pipeline_scheduler
    etl_on = settings.enable_etl_scheduler and postgres_engine is not None

    if not pipeline_on and not etl_on:
        logger.info("파이프라인·ETL 스케줄러 모두 비활성화 또는 PostgreSQL 없음으로 시작하지 않습니다.")
        return None

    if settings.enable_etl_scheduler and postgres_engine is None:
        logger.warning(
            "ETL 스케줄러가 켜져 있으나 PostgreSQL 엔진이 없습니다. ETL 작업은 등록되지 않습니다."
        )

    sched = BackgroundScheduler(timezone="Asia/Seoul")

    if pipeline_on:
        wd = settings.scheduler_weekday.lower()
        sched.add_job(
            _run_job,
            CronTrigger(day_of_week=wd, hour=settings.scheduler_initial_hour, minute=0),
            args=(session_factory, PipelineJob.INITIAL, settings.pipeline_daily_rows),
            id="pipeline_initial_weekly",
            replace_existing=True,
        )
        sched.add_job(
            _run_job,
            CronTrigger(day_of_week=wd, hour=settings.scheduler_completion_hour, minute=0),
            args=(session_factory, PipelineJob.COMPLETION, settings.pipeline_daily_rows),
            id="pipeline_completion_weekly",
            replace_existing=True,
        )
        logger.info(
            "파이프라인 작업 등록, 요일토큰=%s, 초기 시각=%02d시, 완료 계열 시각=%02d시",
            wd,
            settings.scheduler_initial_hour,
            settings.scheduler_completion_hour,
        )

    if etl_on:
        register_etl_jobs(sched, settings, session_factory, postgres_engine)

    sched.start()
    logger.info("백그라운드 스케줄러 기동")
    return sched


def start_weekly_pipeline_scheduler(
    settings: Settings,
    session_factory: "sessionmaker[Session]",
) -> BackgroundScheduler | None:

    return start_background_scheduler(settings, session_factory, postgres_engine=None)
