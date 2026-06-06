import asyncio
from collections.abc import Awaitable, Callable

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class BroadcastManager:
    """Real-time broadcast via Redis Pub/Sub.

    PUBLISH / SUBSCRIBE only — never use LPUSH here.
    One instance per pod subscribes to pattern "room:*" and routes
    messages to local WebSocket connections via the provided callback.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._pubsub = redis.pubsub()
        self._listen_task: asyncio.Task | None = None

    async def start(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Subscribe to all room channels and start the background listener."""
        await self._pubsub.psubscribe("room:*")
        self._listen_task = asyncio.create_task(
            self._listen(callback), name="broadcast-listener"
        )
        logger.info("broadcast_manager.started")

    async def _listen(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        while True:
            try:
                async for message in self._pubsub.listen():
                    if message["type"] != "pmessage":
                        continue
                    channel: str = message["channel"]
                    room_id = channel.removeprefix("room:")
                    await callback(room_id, message["data"])
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("broadcast_manager.listen_error")
                try:
                    await self._pubsub.aclose()
                except Exception:
                    pass
                # Recreate pubsub object
                self._pubsub = self._redis.pubsub()
                # Reconnect after delay
                await asyncio.sleep(2)
                try:
                    await self._pubsub.psubscribe("room:*")
                    logger.info("broadcast_manager.resubscribed")
                except Exception:
                    logger.exception("broadcast_manager.resubscribe_failed")

    async def publish(self, room_id: str, data: str) -> None:
        """Publish a message to a room's Redis Pub/Sub channel."""
        await self._redis.publish(f"room:{room_id}", data)
        logger.debug("broadcast_manager.published", room_id=room_id)

    async def stop(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            await asyncio.gather(self._listen_task, return_exceptions=True)
        await self._pubsub.punsubscribe("room:*")
        await self._pubsub.aclose()
        logger.info("broadcast_manager.stopped")
