"""공유 클라이언트 회귀 테스트 — 요청/재초기화마다 커넥션 풀이 새로 생기지 않는지."""

import pytest
from unittest.mock import AsyncMock, patch

from app.core.utils.redis import AsyncRedisClient


@pytest.mark.asyncio
async def test_redis_init_twice_closes_previous_client():
    with patch("app.core.utils.redis.Redis.from_url") as from_url:
        first, second = AsyncMock(), AsyncMock()
        from_url.side_effect = [first, second]

        await AsyncRedisClient.init("t", "redis://localhost:6379/0")
        await AsyncRedisClient.init("t", "redis://localhost:6379/0")

        first.aclose.assert_awaited_once()
        assert AsyncRedisClient.get_client("t") is second
        await AsyncRedisClient.close_all()


@pytest.mark.asyncio
async def test_token_blacklist_noop_without_shared_redis():
    from app.core.security import token_blacklist

    AsyncRedisClient._instances.clear()
    await token_blacklist.blacklist_token("tok", 10)  # 예외 없이 no-op
    assert await token_blacklist.is_token_blacklisted("tok") is False


def test_boto3_clients_are_cached_per_key():
    with patch("boto3.client") as boto_client:
        boto_client.side_effect = lambda *a, **k: object()
        from app.core.utils.aws.aws_service_util import _boto3_client
        from app.core.utils.aws.s3_presigned_util import S3PresignedUtil

        assert _boto3_client("ses", "ap-northeast-2") is _boto3_client("ses", "ap-northeast-2")
        assert _boto3_client("ses", "ap-northeast-2") is not _boto3_client("ses", "us-east-1")
        assert S3PresignedUtil("b")._client is S3PresignedUtil("b")._client
