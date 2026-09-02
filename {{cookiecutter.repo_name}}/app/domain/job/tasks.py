"""Job 태스크 함수.

runner가 JOB_REGISTRY의 func 경로를 동적 import하여 실행한다.
새 job 추가 시 runner.py의 JOB_REGISTRY에 등록하면 된다.
"""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.core.logger import get_logger

logger = get_logger(__name__)

KST = ZoneInfo("Asia/Seoul")


async def run_ping() -> dict[str, Any]:
    """스케줄러 동작 확인용 테스트 태스크."""
    now = datetime.now(KST).isoformat()
    logger.info("job_completed", job="ping", message="scheduler is alive", kst_now=now)
    return {"message": "pong", "kst_now": now}
