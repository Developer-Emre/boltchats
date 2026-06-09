import asyncio
from collections.abc import Awaitable, Callable

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class MessageConfirmationManager:
    """Subscribe to message:confirmed Redis channel and forward confirmations to clients.
    
    Storage service publishes: { client_message_id, server_id (ObjectId), room_id }
    We route it to the original sender so they can update their optimistic message.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._pubsub = redis.pubsub()
        self._listen_task: asyncio.Task | None = None

    async def start(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        """Subscribe to message confirmations and start listener."""
        await self._pubsub.subscribe("message:confirmed")
        self._listen_task = asyncio.create_task(
            self._listen(callback), name="message-confirmation-listener"
        )
        logger.info("message_confirmation_manager.started")

    async def _listen(self, callback: Callable[[str, str], Awaitable[None]]) -> None:
        while True:
            try:
                async for message in self._pubsub.listen():
                    if message["type"] != "message":
                        continue
                    # Callback receives the raw JSON from storage
                    await callback(message["data"])
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("message_confirmation_manager.listen_error")
                try:
                    await self._pubsub.aclose()
                except Exception:
                    pass
                # Recreate pubsub object
                self._pubsub = self._redis.pubsub()
                # Reconnect after delay
                await asyncio.sleep(2)
                try:
                    await self._pubsub.subscribe("message:confirmed")
                    logger.info("message_confirmation_manager.resubscribed")
                except Exception:
                    logger.exception("message_confirmation_manager.resubscribe_failed")

    async def stop(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            await asyncio.gather(self._listen_task, return_exceptions=True)
        await self._pubsub.unsubscribe("message:confirmed")
        await self._pubsub.aclose()
        logger.info("message_confirmation_manager.stopped")
