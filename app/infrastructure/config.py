import logging
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_dotenv_paths() -> tuple[str, ...]:
    ordered: list[Path] = [
        _PROJECT_ROOT / ".env.example",
        Path.cwd() / ".env",
        _PROJECT_ROOT / ".env",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for p in ordered:
        try:
            rp = p.resolve()
        except OSError:
            continue
        if not rp.is_file():
            continue
        key = str(rp)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return tuple(out)


_DOTENV_FILES = _resolve_dotenv_paths()

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_DOTENV_FILES if _DOTENV_FILES else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_host: str = "127.0.0.1"
    database_port: int = 3306
    database_name: str = "finsight2"
    database_user: str = "finsight"
    database_password: str = "root123"

    scheduler_weekday: str = "mon"
    scheduler_initial_hour: int = 9
    scheduler_completion_hour: int = 16
    enable_pipeline_write: bool = False

    @model_validator(mode="after")
    def _warn_mysql_password_if_needed(self) -> "Settings":
        if (
            self.database_password == ""
            and self.database_user
            and self.database_user.lower() not in {"root"}
        ):
            _logger.warning(
                "DATABASE_PASSWORD 가 비었습니다. MySQL 오류 1045, using password: NO 가 발생할 수 있습니다. "
                "저장소 루트 %s 에 .env 를 두고 DATABASE_PASSWORD 를 설정하세요.",
                _PROJECT_ROOT,
            )
        return self

    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    @property
    def resolved_dotenv_files(self) -> tuple[str, ...]:
        return _DOTENV_FILES

    @property
    def database_url(self) -> str:
        user = quote_plus(self.database_user)
        pwd = quote_plus(self.database_password)
        return (
            f"mysql+pymysql://{user}:{pwd}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}?charset=utf8mb4"
        )
