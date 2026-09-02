"""Middleware Configuration

애플리케이션의 미들웨어를 설정합니다.
- 구조화된 로깅 (structlog)
- 요청 ID 추적
- 성능 모니터링
"""

import base64
import secrets
import time
import uuid
from typing import Callable, Awaitable

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.logger import get_logger
from app.core.middleware.audit_middleware import AuditMiddleware

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어.

    요청 ID 자동 생성, 성능 측정, 에러 로깅을 제공한다.
    """

    # 봇 스캐닝 탐지용 경로 키워드 (WordPress, phpMyAdmin 등)
    SCANNER_PATH_KEYWORDS: set[str] = {
        "wp-includes",
        "wp-admin",
        "wp-login",
        "wp-content",
        "xmlrpc.php",
        "phpmyadmin",
        ".env",
        ".git",
        "cgi-bin",
        "admin/config",
        "setup.php",
        "install.php",
    }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        skip_logging_paths = {"/healthz", "/readyz", "/health"}
        path = request.url.path.lower()
        is_scanner = any(keyword in path for keyword in self.SCANNER_PATH_KEYWORDS)
        should_log = path not in skip_logging_paths and not is_scanner

        request_id = str(uuid.uuid4())

        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_host=request.client.host if request.client else None,
        )

        if should_log:
            log.info("request_started")

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            response.headers["X-Request-ID"] = request_id

            if should_log:
                log.info(
                    "request_completed",
                    status_code=response.status_code,
                    duration_ms=round(process_time * 1000, 2),
                )

            return response

        except Exception as exc:
            process_time = time.perf_counter() - start_time

            log.error(
                "request_failed",
                error=str(exc),
                error_type=type(exc).__name__,
                duration_ms=round(process_time * 1000, 2),
                exc_info=True,
            )

            raise


class SwaggerBasicAuthMiddleware(BaseHTTPMiddleware):
    """Swagger 문서 경로에 HTTP Basic Auth를 적용하는 미들웨어.

    SWAGGER_PASSWORD가 설정되어 있을 때만 인증을 요구한다.
    """

    PROTECTED_PATHS: set[str] = {"/api/docs", "/api/docs/oauth2-redirect", "/api/redoc", "/api/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path not in self.PROTECTED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                username, password = decoded.split(":", 1)
                if secrets.compare_digest(username, settings.SWAGGER_USERNAME) and secrets.compare_digest(password, settings.SWAGGER_PASSWORD):
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Swagger Docs"'},
            content="Unauthorized",
        )


def setup_middleware(app: FastAPI) -> None:
    """미들웨어를 설정한다.

    미들웨어 실행 순서:
    1. RequestLoggingMiddleware (가장 먼저 실행)
    2. CORSMiddleware (CORS 정책 처리)
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.add_middleware(AuditMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    if settings.SWAGGER_PASSWORD:
        app.add_middleware(SwaggerBasicAuthMiddleware)

    logger.info(
        "middleware_setup_completed",
        environment=settings.ENVIRONMENT,
        log_level=settings.LOG_LEVEL,
    )
