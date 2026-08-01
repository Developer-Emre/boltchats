import asyncio
from datetime import datetime
from typing import Optional
import structlog
from fastapi import WebSocket
from aioredis import Redis

logger = structlog.get_logger()


class ConnectionManager:
    """
    Manages active WebSocket connections with:
    - Multi-connection support per user
    - Room/channel subscriptions
    - Redis-backed presence tracking for distributed systems
    - Broadcast capabilities
    """

    def __init__(self, redis: Redis | None = None) -> None:
        # Local in-memory tracking
        # connection_id -> { websocket, user_id, rooms, connected_at, message_count }
        self._connections: dict[str, dict] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self.redis = redis

    async def _get_lock(self, connection_id: str) -> asyncio.Lock:
        """Get or create a lock for a connection"""
        if connection_id not in self._locks:
            self._locks[connection_id] = asyncio.Lock()
        return self._locks[connection_id]

    async def connect(
        self,
        ws: WebSocket,
        user_id: str,
        connection_id: str,
    ) -> None:
        """Register a new WebSocket connection"""
        lock = await self._get_lock(connection_id)
        async with lock:
            await ws.accept()

            self._connections[connection_id] = {
                "websocket": ws,
                "user_id": user_id,
                "rooms": set(),
                "connected_at": datetime.utcnow(),
                "message_count": 0,
            }

            # Track in Redis if available
            if self.redis:
                presence_key = f"presence:{user_id}"
                await self.redis.sadd(presence_key, connection_id)
                await self.redis.expire(presence_key, 3600)

            logger.info(
                "websocket_connected",
                connection_id=connection_id,
                user_id=user_id,
                active_connections=len(self._connections),
            )

    def disconnect(self, connection_id: str, ws: WebSocket) -> None:
        """
        Remove connection only if it belongs to this WebSocket.
        Prevents race conditions where a newer connection is incorrectly removed.
        """
        if connection_id not in self._connections:
            return

        conn_info = self._connections[connection_id]
        if conn_info["websocket"] is not ws:
            return

        user_id = conn_info["user_id"]
        rooms = list(conn_info["rooms"])

        # Remove from all subscribed rooms
        for room_id in rooms:
            self._connections[connection_id]["rooms"].discard(room_id)

        del self._connections[connection_id]

        logger.info(
            "websocket_disconnected",
            connection_id=connection_id,
            user_id=user_id,
            active_connections=len(self._connections),
        )

    async def subscribe_room(
        self,
        connection_id: str,
        room_id: str,
    ) -> None:
        """Subscribe connection to a room"""
        if connection_id not in self._connections:
            return

        conn_info = self._connections[connection_id]
        conn_info["rooms"].add(room_id)

        # Track in Redis if available
        if self.redis:
            room_key = f"room:{room_id}:members"
            await self.redis.sadd(room_key, connection_id)
            await self.redis.expire(room_key, 86400)

        logger.info(
            "room_subscribed",
            connection_id=connection_id,
            room_id=room_id,
            user_id=conn_info["user_id"],
        )

    async def unsubscribe_room(
        self,
        connection_id: str,
        room_id: str,
    ) -> None:
        """Unsubscribe connection from a room"""
        if connection_id not in self._connections:
            return

        conn_info = self._connections[connection_id]
        conn_info["rooms"].discard(room_id)

        # Remove from Redis if available
        if self.redis:
            room_key = f"room:{room_id}:members"
            await self.redis.srem(room_key, connection_id)

        logger.info(
            "room_unsubscribed",
            connection_id=connection_id,
            room_id=room_id,
            user_id=conn_info["user_id"],
        )

    async def broadcast_to_room(
        self,
        room_id: str,
        message: dict,
        exclude_user: Optional[str] = None,
    ) -> dict:
        """
        Broadcast message to all users in a room.
        Returns delivery stats.
        """
        sent = 0
        failed = 0

        for connection_id, conn_info in self._connections.items():
            if room_id not in conn_info["rooms"]:
                continue

            # Skip if sender requested exclusion
            if exclude_user and conn_info["user_id"] == exclude_user:
                continue

            try:
                await conn_info["websocket"].send_json(message)
                sent += 1
                conn_info["message_count"] += 1
            except Exception as e:
                logger.warning(
                    "broadcast_send_failed",
                    connection_id=connection_id,
                    room_id=room_id,
                    error=str(e),
                )
                failed += 1

        return {
            "room_id": room_id,
            "sent": sent,
            "failed": failed,
            "total": sent + failed,
        }

    async def send_to_user(
        self,
        user_id: str,
        message: dict,
    ) -> dict:
        """Send message to all active connections of a user"""
        sent = 0
        failed = 0

        for connection_id, conn_info in self._connections.items():
            if conn_info["user_id"] != user_id:
                continue

            try:
                await conn_info["websocket"].send_json(message)
                sent += 1
                conn_info["message_count"] += 1
            except Exception as e:
                logger.warning(
                    "user_send_failed",
                    connection_id=connection_id,
                    user_id=user_id,
                    error=str(e),
                )
                failed += 1

        return {
            "user_id": user_id,
            "sent": sent,
            "failed": failed,
        }

    async def get_room_stats(self, room_id: str) -> dict:
        """Get stats for a room"""
        members = set()
        for conn_info in self._connections.values():
            if room_id in conn_info["rooms"]:
                members.add(conn_info["user_id"])

        return {
            "room_id": room_id,
            "active_connections": len(
                [c for c in self._connections.values() if room_id in c["rooms"]]
            ),
            "active_users": len(members),
        }

    def get_user_connections(self, user_id: str) -> list[str]:
        """Get all active connection IDs for a user"""
        return [
            conn_id
            for conn_id, conn_info in self._connections.items()
            if conn_info["user_id"] == user_id
        ]

    def get_active_users(self) -> int:
        """Get count of active unique users"""
        users = set()
        for conn_info in self._connections.values():
            users.add(conn_info["user_id"])
        return len(users)

    def active_count(self) -> int:
        """Get total active connections"""
        return len(self._connections)

    async def heartbeat(self) -> int:
        """Send heartbeat to all connections. Returns disconnected count."""
        disconnected = []

        for connection_id, conn_info in self._connections.items():
            try:
                await conn_info["websocket"].send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception as e:
                logger.warning(
                    "heartbeat_failed",
                    connection_id=connection_id,
                    error=str(e),
                )
                disconnected.append(connection_id)

        # Clean up dead connections
        for connection_id in disconnected:
            if connection_id in self._connections:
                ws = self._connections[connection_id]["websocket"]
                self.disconnect(connection_id, ws)

        return len(disconnected)
