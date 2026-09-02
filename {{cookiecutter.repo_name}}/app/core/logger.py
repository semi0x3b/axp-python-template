"""Logging Configuration

애플리케이션의 로깅을 설정합니다.
structlog를 사용하며, 표준 logging과도 호환됩니다.
"""

import logging
import sys
from datetime import datetime
from typing import Optional

import structlog
from zoneinfo import ZoneInfo

from app.core.config import settings


class KSTFormatter(logging.Formatter):
    """KST(한국 표준시)를 사용하는 로깅 포맷터."""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self.kst = ZoneInfo("Asia/Seoul")

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created, tz=self.kst)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.isoformat()


def add_kst_timestamp(logger, method_name, event_dict):
    """KST 타임스탬프를 추가하는 structlog 프로세서."""
    kst = ZoneInfo("Asia/Seoul")
    kst_time = datetime.now(kst)

    event_dict["timestamp"] = kst_time.isoformat()

    if "_record" in event_dict:
        record = event_dict["_record"]
        if hasattr(record, "created"):
            created_kst = datetime.fromtimestamp(record.created, tz=kst)
            event_dict["time"] = created_kst.strftime("%Y-%m-%d %H:%M:%S")
        else:
            event_dict["time"] = kst_time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        event_dict["time"] = kst_time.strftime("%Y-%m-%d %H:%M:%S")

    return event_dict


class HealthCheckFilter(logging.Filter):
    """헬스체크 경로(/healthz, /readyz, /health)의 액세스 로그를 필터링한다."""

    HEALTH_PATHS = {"/healthz", "/readyz", "/health"}

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        return not any(path in message for path in self.HEALTH_PATHS)


def configure_logger() -> None:
    """Structlog 및 표준 Logging을 설정한다.

    프로덕션 환경에서는 JSON 포맷, 개발 환경에서는 컬러 콘솔 출력을 사용한다.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        add_kst_timestamp,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    is_production = settings.ENVIRONMENT in ["prod"]

    if is_production:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(sort_keys=True, ensure_ascii=False),
        ]
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.DEBUG)

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 표준 라이브러리 로깅 설정 (KST 포맷터)
    kst_formatter = KSTFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(kst_formatter)
    root_logger.addHandler(console_handler)

    # Uvicorn 로거 설정
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(log_level)
    for handler in uvicorn_logger.handlers:
        handler.setFormatter(kst_formatter)

    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(logging.WARNING if is_production else logging.INFO)
    uvicorn_access_logger.addFilter(HealthCheckFilter())
    for handler in uvicorn_access_logger.handlers:
        handler.setFormatter(kst_formatter)

    # SQLAlchemy 로거
    is_local = settings.ENVIRONMENT == "local"
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if is_local else logging.WARNING)

    # 외부 라이브러리 로거
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """structlog 로거를 반환한다.

    Args:
        name: 로거 이름 (선택)

    Returns:
        structlog.BoundLogger: 설정된 로거
    """
    return structlog.get_logger(name)
