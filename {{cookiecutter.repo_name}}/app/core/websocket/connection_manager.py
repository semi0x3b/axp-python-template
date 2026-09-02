"""WebSocket 연결 관리 + Redis Pub/Sub 브로드캐스트.

인메모리 dict로 로컬 연결을 관리하고,
Redis Pub/Sub로 다중 인스턴스 간 메시지를 중계한다.
"""

import asyncio
import json
from typing import Any

from fastapi import WebSocket
from redis.asyncio import Redis

from app.core.logger import get_logger

logger = get_logger(__name__)

CHAT_CHANNEL = "chat:messages"


class ConnectionManager:
    """WebSocket 연결 매니저.

    단일 인스턴스로 사용. 앱 시작 시 subscribe_redis()를 호출하여
    Redis Pub/Sub 리스닝을 시작한다.
    """

    def __init__(self) -> None:
        self._connections: dict[int, WebSocket] = {}  # user_id → WebSocket
        self._pubsub_task: asyncio.Task | None = None
        self._redis: Redis | None = None

    # ──────────────────────────────────────────────
    # 로컬 연결 관리
    # ──────────────────────────────────────────────
    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """WebSocket 연결을 수락하고 등록한다."""
        await websocket.accept()
        # 기존 연결이 있으면 닫기 (중복 세션 방지)
        old = self._connections.get(user_id)
        if old is not None:
            try:
                await old.close(code=4001, reason="새 연결로 대체됨")
            except Exception:
                pass
        self._connections[user_id] = websocket
        logger.info("ws_connected", user_id=user_id)

    def disconnect(self, user_id: int) -> None:
        """WebSocket 연결을 해제한다."""
        self._connections.pop(user_id, None)
        logger.info("ws_disconnected", user_id=user_id)

    def is_online(self, user_id: int) -> bool:
        """사용자가 현재 연결 중인지 확인한다."""
        return user_id in self._connections

    async def send_to_user(self, user_id: int, data: dict[str, Any]) -> bool:
        """로컬 연결된 사용자에게 메시지를 전송한다.

        Returns:
            전송 성공 여부.
        """
        ws = self._connections.get(user_id)
        if ws is None:
            return False
        try:
            await ws.send_json(data)
            return True
        except Exception:
            self.disconnect(user_id)
            return False

    # ──────────────────────────────────────────────
    # Redis Pub/Sub (다중 인스턴스)
    # ──────────────────────────────────────────────
    async def start_redis_subscriber(self, redis: Redis) -> None:
        """Redis Pub/Sub 리스닝을 시작한다."""
        self._redis = redis
        self._pubsub_task = asyncio.create_task(self._listen_redis())

    async def stop_redis_subscriber(self) -> None:
        """Redis Pub/Sub 리스닝을 중지한다."""
        if self._pubsub_task is not None:
            self._pubsub_task.cancel()
            try:
                await self._pubsub_task
            except asyncio.CancelledError:
                pass
            self._pubsub_task = None

    async def publish(self, target_user_id: int, data: dict[str, Any]) -> None:
        """Redis를 통해 메시지를 퍼블리시한다.

        로컬에 연결된 사용자면 직접 전송하고, 아니면 Redis로 중계한다.
        """
        sent = await self.send_to_user(target_user_id, data)
        if not sent and self._redis is not None:
            payload = json.dumps({"target_user_id": target_user_id, **data}, ensure_ascii=False)
            await self._redis.publish(CHAT_CHANNEL, payload)

    async def _listen_redis(self) -> None:
        """Redis Pub/Sub 채널에서 메시지를 수신하여 로컬 연결에 전달한다."""
        if self._redis is None:
            return

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(CHAT_CHANNEL)
        logger.info("redis_pubsub_subscribed", channel=CHAT_CHANNEL)

        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    raw = message["data"]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8")
                    payload = json.loads(raw)
                    target_user_id = payload.pop("target_user_id", None)
                    if target_user_id is not None:
                        await self.send_to_user(target_user_id, payload)
                except Exception as e:
                    logger.error("redis_pubsub_error", error=str(e))
        except asyncio.CancelledError:
            await pubsub.unsubscribe(CHAT_CHANNEL)
            await pubsub.close()
            raise


# 싱글톤 인스턴스
manager = ConnectionManager()
