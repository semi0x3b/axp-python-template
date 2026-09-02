import json
from typing import Optional, Dict, Callable, Awaitable, Any, Union

from redis.asyncio import Redis
from redis.exceptions import TimeoutError, ConnectionError, RedisError

from app.core.enum.redis_key import RedisKey
from app.core.logger import get_logger

logger = get_logger(__name__)


class AsyncRedisClient:
    _instances: Dict[str, Redis] = {}

    @classmethod
    def init(
        cls,
        name: str,
        url: str,
        password: Optional[str] = None,
    ):
        """Redis 클라이언트를 URL 기반으로 초기화합니다.

        Args:
            name: Redis 인스턴스 이름 (예: 'main', 'progress')
            url: Redis URL (예: redis://localhost:6379/0)
            password: Redis 비밀번호 (선택)
        """
        cls._instances[name] = Redis.from_url(
            url,
            password=password,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=5,
        )

    @classmethod
    def get_client(cls, name: str = "default") -> Redis:
        if name not in cls._instances:
            raise RuntimeError(f"Redis instance '{name}' is not initialized.")
        return cls._instances[name]

    @classmethod
    async def close_all(cls):
        for redis in cls._instances.values():
            if redis is not None:
                await redis.close()
        cls._instances.clear()


async def get_redis_main() -> Redis:
    # lifespan에서 init 했으니 여기서는 가져오기만
    from app.core.config import settings

    return AsyncRedisClient.get_client(settings.REDIS_MAIN_NAME)


async def get_redis_chat() -> Redis:
    """채팅 전용 Redis 클라이언트를 반환한다."""
    from app.core.config import settings

    return AsyncRedisClient.get_client(settings.REDIS_CHAT_NAME)


async def get_with_fallback(
    redis_client: Redis,
    key: str,
    db_fallback_func: Callable[[], Awaitable[Any]],  # dict/list/str 반환 허용
    ttl: int | None = 3600,
    name: str = "default",
) -> Any:
    """
    - Redis에서 가져오면: 문자열이면 JSON decode 후 객체로 리턴(실패시 원문 반환)
    - 캐시 미스/에러면: db_fallback_func() 실행 → 캐시에 '문자열'로 저장 → '객체'로 리턴
    """
    redis_ok = True
    try:
        cached = await redis_client.get(key)
        if cached is not None:
            # decode to object if possible
            try:
                return json.loads(cached)
            except Exception:
                return cached  # 이미 원문이 필요한 경우
    except (TimeoutError, ConnectionError, RedisError) as e:
        logger.warning(f"[{name}] Redis GET failed: {e}")
        redis_ok = False

    # 3) DB/외부 API로 대체 조회
    value = await db_fallback_func()

    # 4) 캐시에 문자열로 저장(리턴은 객체 그대로)
    if redis_ok:
        try:
            to_store: Optional[str]
            if isinstance(value, (dict, list)):
                to_store = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, str):
                to_store = value
            else:
                # 기타 타입은 문자열화
                to_store = json.dumps(value, ensure_ascii=False, default=str)
            # ex=None 이면 무제한(만료 없음)
            await redis_client.set(key, to_store, ex=ttl)
        except (TimeoutError, ConnectionError, RedisError) as e:
            logger.warning(f"[{name}] Redis SET failed: {e}")
        except Exception as e:
            logger.warning(f"[{name}] Cache serialize failed: {e}")

    return value


def json_dumps_aware(data: dict) -> str:
    def _default(o: Any):
        from datetime import datetime

        if isinstance(o, datetime):
            return o.isoformat()
        return str(o)

    import json

    return json.dumps(data, ensure_ascii=False, default=_default)


async def get_json_from_redis(
    redis,
    key_template: RedisKey,
    **fmt: Any,
) -> Optional[Union[dict, list]]:
    """
    RedisKey 템플릿과 포맷 변수를 받아, Redis에서 값을 읽어 JSON으로 반환.
    - 없으면 None
    - bytes/str 모두 처리
    - JSON 파싱 실패 시 None (로깅)
    """
    try:
        key = key_template.format(**fmt)
        raw = await redis.get(key)
        if raw is None:
            return None

        # aioredis는 보통 bytes를 반환하므로 디코딩
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="ignore")

        # 이미 dict/list 형태로 들어오는 경우는 드묾. 그래도 안전 처리
        if isinstance(raw, (dict, list)):
            return raw

        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                logger.error(f"[Redis] JSON decode failed for key={key} value(sample)={raw[:200]!r}")
                return None
    except Exception as e:
        logger.error(f"[Redis] Failed to get : {e}")

    return None
