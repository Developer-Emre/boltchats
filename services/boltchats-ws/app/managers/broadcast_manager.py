import asyncio
from collections.abc import Awaitable, Callable

import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class BroadcastManager:
    """Real-time broadcast via Redis Pub/Sub.

    PUBLISH / SUBSCRIBE only — never use LPUSH here.
    One instance per pod subscribes to patterns:
      - "room:*" (v1 - backward compatibility)
      - "workspace:*" (v2 - workspace-level events)
      - "channel:*" (v2 - channel events)
      - "dm:*" (v2 - direct message events)
    
    Routes messages to local WebSocket connections via callback.
    """

    def __init__(self, redis: Redis) -> None:
        self._redis = redis
        self._pubsub = redis.pubsub()
        self._listen_task: asyncio.Task | None = None

    async def start(self, callback: Callable[[str, str, str], Awaitable[None]]) -> None:
        """Subscribe to all broadcast channels and start the background listener."""
        # Subscribe to both v1 (room) and v2 (workspace, channel, dm) patterns
        await self._pubsub.psubscribe("room:*", "workspace:*", "channel:*", "dm:*")
        self._listen_task = asyncio.create_task(
            self._listen(callback), name="broadcast-listener"
        )
        logger.info("broadcast_manager.started")

    async def _listen(self, callback: Callable[[str, str, str], Awaitable[None]]) -> None:
        while True:
            try:
                async for message in self._pubsub.listen():
                    if message["type"] != "pmessage":
                        continue
                    channel: str = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                    data: str = message["data"].decode() if isinstance(message["data"], bytes) else message["data"]
                    
                    # Parse channel to extract context type and ID
                    if channel.startswith("room:"):
                        context_type = "room"
                        context_id = channel.removeprefix("room:")
                    elif channel.startswith("workspace:"):
                        context_type = "workspace"
                        context_id = channel.removeprefix("workspace:")
                    elif channel.startswith("channel:"):
                        context_type = "channel"
                        context_id = channel.removeprefix("channel:")
                    elif channel.startswith("dm:"):
                        context_type = "dm"
                        context_id = channel.removeprefix("dm:")
                    else:
                        continue
                    
                    await callback(context_type, context_id, data)
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
                    await self._pubsub.psubscribe("room:*", "workspace:*", "channel:*", "dm:*")
                    logger.info("broadcast_manager.resubscribed")
                except Exception:
                    logger.exception("broadcast_manager.resubscribe_failed")

    async def publish_room(self, room_id: str, data: str) -> None:
        """Publish a message to a room's Redis Pub/Sub channel (v1)."""
        await self._redis.publish(f"room:{room_id}", data)
        logger.debug("broadcast_manager.published_room", room_id=room_id)

    async def publish_workspace(self, workspace_id: str, data: str) -> None:
        """Publish a message to a workspace's Redis Pub/Sub channel (v2)."""
        await self._redis.publish(f"workspace:{workspace_id}", data)
        logger.debug("broadcast_manager.published_workspace", workspace_id=workspace_id)

    async def publish_channel(self, channel_id: str, data: str) -> None:
        """Publish a message to a channel's Redis Pub/Sub channel (v2)."""
        await self._redis.publish(f"channel:{channel_id}", data)
        logger.debug("broadcast_manager.published_channel", channel_id=channel_id)

    async def publish_dm(self, dm_id: str, data: str) -> None:
        """Publish a message to a DM group's Redis Pub/Sub channel (v2)."""
        await self._redis.publish(f"dm:{dm_id}", data)
        logger.debug("broadcast_manager.published_dm", dm_id=dm_id)

    async def stop(self) -> None:
        if self._listen_task is not None:
            self._listen_task.cancel()
            await asyncio.gather(self._listen_task, return_exceptions=True)
        await self._pubsub.punsubscribe("room:*", "workspace:*", "channel:*", "dm:*")
        await self._pubsub.aclose()
        logger.info("broadcast_manager.stopped")
