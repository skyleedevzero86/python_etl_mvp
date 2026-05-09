from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_postgres_engine_from_settings(settings: Settings) -> Engine:
    return create_engine(
        settings.postgres_database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
