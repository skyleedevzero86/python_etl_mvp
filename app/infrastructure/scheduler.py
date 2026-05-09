import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.pipeline_service import PipelineApplicationService
from app.domain.enums import PipelineJob
from app.infrastructure.config import Settings
from app.infrastructure.repositories.pipeline_mysql import MysqlPipelineRepository

if TYPE_CHECKING:
    from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)


def _run_job(factory: "sessionmaker[Session]", job: PipelineJob) -> None:
    session = factory()
    try:
        repo = MysqlPipelineRepository(session)
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


def start_weekly_pipeline_scheduler(
    settings: Settings,
    session_factory: "sessionmaker[Session]",
) -> BackgroundScheduler | None:
    if not settings.enable_pipeline_write:
        logger.info("파이프라인 쓰기 비활성화 상태라 스케줄러를 시작하지 않습니다.")
        return None

    sched = BackgroundScheduler(timezone="Asia/Seoul")
    wd = settings.scheduler_weekday.lower()
    sched.add_job(
        _run_job,
        CronTrigger(day_of_week=wd, hour=settings.scheduler_initial_hour, minute=0),
        args=(session_factory, PipelineJob.INITIAL),
        id="pipeline_initial_weekly",
        replace_existing=True,
    )
    sched.add_job(
        _run_job,
        CronTrigger(day_of_week=wd, hour=settings.scheduler_completion_hour, minute=0),
        args=(session_factory, PipelineJob.COMPLETION),
        id="pipeline_completion_weekly",
        replace_existing=True,
    )
    sched.start()
    logger.info(
        "스케줄러 기동, 요일토큰=%s, 초기 시각=%02d시, 완료 계열 시각=%02d시",
        wd,
        settings.scheduler_initial_hour,
        settings.scheduler_completion_hour,
    )
    return sched
