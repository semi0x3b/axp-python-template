"""FastAPI Application Factory

애플리케이션 생성 및 초기화를 담당합니다.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.enum.environment import Environment
from app.core.logger import configure_logger, get_logger
from app.core.middleware import setup_middleware
from app.core.exception.handlers import setup_exception_handlers
from app.core.health import router as health_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 lifespan 이벤트."""
    from app.core.utils.redis import AsyncRedisClient
    from app.core.websocket.connection_manager import manager

    configure_logger()

    # Redis 초기화 (메인)
    await AsyncRedisClient.init(
        name=settings.REDIS_MAIN_NAME,
        url=settings.redis_url,
        password=settings.redis_password_or_none,
    )
    logger.info("redis_initialized", name=settings.REDIS_MAIN_NAME)

    # Redis 초기화 (채팅/알림 전용 — 같은 서버, DB 분리)
    await AsyncRedisClient.init(
        name=settings.REDIS_CHAT_NAME,
        url=settings.redis_chat_url,
        password=settings.redis_password_or_none,
    )
    logger.info("redis_initialized", name=settings.REDIS_CHAT_NAME)

    # WebSocket Redis Pub/Sub 시작
    redis_chat = AsyncRedisClient.get_client(settings.REDIS_CHAT_NAME)
    await manager.start_redis_subscriber(redis_chat)

    logger.info(
        "application_started",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
    )
    yield

    # WebSocket Redis Pub/Sub 종료
    await manager.stop_redis_subscriber()

    # DB 엔진 종료 (커넥션 풀 정리)
    from app.db.connection import engine

    await engine.dispose()

    # Redis 종료
    await AsyncRedisClient.close_all()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리."""
    # APP_SERVICE 환경변수로 라우터/태그 분기 ({{cookiecutter.container_prefix}} / backoffice / job / all)
    service = os.getenv("APP_SERVICE", "all").lower()

    # 태그 메타데이터는 도메인 확정 후 채워넣는다.
    tags_metadata: list[dict] = []

    title_map = {
        "{{cookiecutter.container_prefix}}": "{{cookiecutter.project_name}} API",
        "backoffice": "{{cookiecutter.project_name}} Backoffice API",
        "job": "{{cookiecutter.project_name}} Job API",
        "all": settings.APP_TITLE,
    }
    description_map = {
        "{{cookiecutter.container_prefix}}": "{{cookiecutter.project_description}}",
        "backoffice": "{{cookiecutter.project_name}} 백오피스 API",
        "job": "{{cookiecutter.project_name}} 배치 작업 API",
        "all": "{{cookiecutter.project_description}}",
    }

    # 운영 환경에서는 Swagger/ReDoc/OpenAPI 완전 비활성화
    if settings.ENVIRONMENT == Environment.production:
        docs_url = None
        redoc_url = None
        openapi_url = None
    else:
        docs_url = "/api/docs"
        redoc_url = "/api/redoc"
        openapi_url = "/api/openapi.json"

    app = FastAPI(
        title=title_map.get(service, settings.APP_TITLE),
        description=description_map.get(service, ""),
        version=settings.APP_VERSION,
        openapi_tags=tags_metadata,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    setup_middleware(app)
    setup_exception_handlers(app)

    app.include_router(health_router)

    # TODO: 도메인 라우터 include
    # if service in ("{{cookiecutter.container_prefix}}", "all"):
    #     from app.domain.{{cookiecutter.container_prefix}}.{{cookiecutter.container_prefix}}_router import router as main_router
    #     app.include_router(main_router)
    # if service in ("backoffice", "all"):
    #     from app.domain.backoffice.backoffice_router import router as backoffice_router
    #     app.include_router(backoffice_router)

    logger.info("routers_loaded", service=service)

    return app
