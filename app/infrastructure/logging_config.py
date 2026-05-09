from __future__ import annotations

import logging
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / "logs"


def log_dir() -> Path:
    return _LOG_DIR


def setup_uncaught_exception_logfile() -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    out = _LOG_DIR / "last_crash.txt"

    def _hook(exc_type, exc, tb):
        try:
            with out.open("w", encoding="utf-8") as fp:
                fp.write(f"{getattr(exc_type, '__name__', exc_type)}: {exc}\n\n")
                traceback.print_exception(exc_type, exc, tb, file=fp)
        except OSError:
            pass
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _hook
    return out


def configure_root_logging(level: int = logging.INFO) -> Path:
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _LOG_DIR / "app.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(level)
    stderr_handler.setFormatter(fmt)
    root.addHandler(stderr_handler)

    logging.captureWarnings(True)
    return log_path
