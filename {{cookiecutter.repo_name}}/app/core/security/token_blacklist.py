"""JWT 토큰 블랙리스트 (Redis 기반).

로그아웃 시 토큰을 블랙리스트에 추가하여 재사용을 방지한다.
lifespan 에서 초기화한 공유 Redis 클라이언트(main)를 그대로 쓴다.
Redis 가 초기화되지 않았거나 장애여도 앱은 정상 동작한다 (graceful degradation).
"""

import hashlib
from typing import Optional

from redis.asyncio import Redis

from app.core.logger import get_logger
from app.core.utils.redis import AsyncRedisClient

logger = get_logger(__name__)

_KEY_PREFIX = "token:blacklist:"


def _shared_client() -> Optional[Redis]:
    from app.core.config import settings

    try:
        return AsyncRedisClient.get_client(settings.REDIS_MAIN_NAME)
    except RuntimeError:
        return None


def _token_key(token: str) -> str:
    """토큰의 SHA-256 해시를 키로 사용한다."""
    return f"{_KEY_PREFIX}{hashlib.sha256(token.encode()).hexdigest()}"


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    """토큰을 블랙리스트에 추가한다. TTL은 토큰 잔여 만료 시간."""
    client = _shared_client()
    if client is None:
        return
    try:
        await client.set(_token_key(token), "1", ex=ttl_seconds)
    except Exception as e:
        logger.warning("token_blacklist_set_failed", error=str(e))


async def is_token_blacklisted(token: str) -> bool:
    """토큰이 블랙리스트에 있는지 확인한다. Redis 장애 시 False 반환."""
    client = _shared_client()
    if client is None:
        return False
    try:
        return await client.exists(_token_key(token)) > 0
    except Exception as e:
        logger.warning("token_blacklist_check_failed", error=str(e))
        return False
