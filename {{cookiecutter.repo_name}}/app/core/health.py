"""Health Check Endpoints

Kubernetes liveness/readiness probe를 위한 헬스 체크 엔드포인트.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.db.connection import engine
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthStatus(BaseModel):
    """헬스 체크 응답 모델."""

    status: str
    timestamp: str
    environment: str
    services: Dict[str, Dict[str, Any]]


async def check_db_connection() -> Dict[str, Any]:
    """데이터베이스 연결 상태를 확인한다."""
    sa_logger = logging.getLogger("sqlalchemy.engine")
    original_level = sa_logger.level
    sa_logger.setLevel(logging.WARNING)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "healthy": True,
        }
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        return {
            "status": "error",
            "healthy": False,
            "message": str(e),
        }
    finally:
        sa_logger.setLevel(original_level)


@router.get("/healthz", response_model=HealthStatus, include_in_schema=False)
async def liveness_probe() -> HealthStatus:
    """Liveness Probe — 애플리케이션이 살아있는지 확인한다."""
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.ENVIRONMENT,
        services={
            "api": {
                "status": "running",
                "healthy": True,
            }
        },
    )


@router.get("/readyz", response_model=HealthStatus, include_in_schema=False)
async def readiness_probe(response: Response) -> HealthStatus:
    """Readiness Probe — 트래픽을 받을 준비가 되었는지 확인한다."""
    db_status = await check_db_connection()

    services = {
        "database": db_status,
    }

    all_healthy = all(svc["healthy"] for svc in services.values())

    if all_healthy:
        overall_status = "healthy"
        status_code = status.HTTP_200_OK
    else:
        overall_status = "unhealthy"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    response.status_code = status_code

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        environment=settings.ENVIRONMENT,
        services=services,
    )


@router.get("/health", response_model=HealthStatus, include_in_schema=False)
async def health_check(response: Response) -> HealthStatus:
    """상세 헬스 체크 — readyz와 동일하지만 사람이 읽기 쉬운 엔드포인트."""
    return await readiness_probe(response)
