"""테스트용 공용 픽스처.

`.env` 없이도 돌도록 테스트용 env 기본값을 import 이전에 주입한다.
DB는 docker compose 의 `db-test`(5433, tmpfs) 를 사용한다 — `make up` 필요.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

os.environ.setdefault("ENVIRONMENT", "local")
os.environ.setdefault("USE_ENV_FILE", "false")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5433")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "postgres")
os.environ.setdefault("DB_NAME", "{{cookiecutter.db_name}}_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENCRYPTION_KEY", "ab" * 32)
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_PASSWORD", "")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.model  # noqa: F401 — 모든 모델 metadata 등록
from app.core.config import settings
from app.db.base import Base
from app.db.connection import get_session


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """DB 없이 앱만 띄우는 클라이언트 — 의존성을 mock 하는 단위 테스트용."""
    from app.main import create_app

    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """세션 1회: public 스키마를 갈아엎고 모델 metadata 로 재생성."""
    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.exec_driver_sql("DROP SCHEMA public CASCADE")
        await conn.exec_driver_sql("CREATE SCHEMA public")
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as s:
        yield s
        await s.rollback()


@pytest.fixture(scope="function")
def clean_db(test_engine):
    """각 통합 테스트 전 public 스키마 전 테이블 truncate.

    pg_tables 동적 조회 — 신규 테이블 추가 시 자동 반영.
    동기 드라이버를 써서 asyncio 루프 호환성 문제를 피한다.
    """
    import psycopg2

    _ = test_engine  # 스키마 생성 후 실행 보장

    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        dbname=os.environ["DB_NAME"],
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT string_agg(quote_ident(tablename), ', ') FROM pg_tables WHERE schemaname = 'public'")
            tables = cur.fetchone()[0]
            if tables:
                cur.execute(f"TRUNCATE {tables} RESTART IDENTITY CASCADE")
    finally:
        conn.close()
    yield


@asynccontextmanager
async def _make_client(service: str, engine) -> AsyncGenerator[AsyncClient, None]:
    """APP_SERVICE 를 바꿔 앱을 다시 만들고 세션 의존성을 테스트 엔진으로 교체."""
    prev = os.environ.get("APP_SERVICE")
    os.environ["APP_SERVICE"] = service
    try:
        from importlib import reload

        import app.main as main_module

        reload(main_module)
        fastapi_app = main_module.create_app()

        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def _override_session():
            async with session_factory() as s:
                try:
                    yield s
                    await s.commit()
                except Exception:
                    await s.rollback()
                    raise

        fastapi_app.dependency_overrides[get_session] = _override_session
        async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as client:
            yield client
    finally:
        if prev is None:
            os.environ.pop("APP_SERVICE", None)
        else:
            os.environ["APP_SERVICE"] = prev


@pytest_asyncio.fixture
async def main_client(test_engine, clean_db) -> AsyncGenerator[AsyncClient, None]:
    async with _make_client("{{cookiecutter.container_prefix}}", test_engine) as client:
        yield client


@pytest_asyncio.fixture
async def backoffice_client(test_engine, clean_db) -> AsyncGenerator[AsyncClient, None]:
    async with _make_client("backoffice", test_engine) as client:
        yield client
