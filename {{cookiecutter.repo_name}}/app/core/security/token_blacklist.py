"""JWT 토큰 블랙리스트 (Redis 기반).

로그아웃 시 토큰을 블랙리스트에 추가하여 재사용을 방지한다.
Redis가 비활성 상태여도 앱은 정상 동작한다 (graceful degradation).
"""

import hashlib
from typing import Optional

from redis.asyncio import Redis

from app.core.logger import get_logger

logger = get_logger(__name__)

_redis_client: Optional[Redis] = None

_KEY_PREFIX = "token:blacklist:"


async def init_blacklist_redis(url: str) -> None:
    """Redis 클라이언트를 초기화한다."""
    global _redis_client
    try:
        _redis_client = Redis.from_url(url, decode_responses=True, socket_timeout=5)
        await _redis_client.ping()
        logger.info("token_blacklist_redis_connected")
    except Exception as e:
        logger.warning("token_blacklist_redis_unavailable", error=str(e))
        _redis_client = None


async def close_blacklist_redis() -> None:
    """Redis 연결을 종료한다."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def _token_key(token: str) -> str:
    """토큰의 SHA-256 해시를 키로 사용한다."""
    return f"{_KEY_PREFIX}{hashlib.sha256(token.encode()).hexdigest()}"


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    """토큰을 블랙리스트에 추가한다. TTL은 토큰 잔여 만료 시간."""
    if _redis_client is None:
        return
    try:
        await _redis_client.set(_token_key(token), "1", ex=ttl_seconds)
    except Exception as e:
        logger.warning("token_blacklist_set_failed", error=str(e))


async def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인한다. Redis 장애 시 False 반환."""
    if _redis_client is None:
        return False
    try:
        return await _redis_client.exists(_token_key(token)) > 0
    except Exception as e:
        logger.warning("token_blacklist_check_failed", error=str(e))
        return False
