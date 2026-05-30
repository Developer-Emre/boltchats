import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


class ConnectionManager:
    """In-memory registry of active WebSocket connections (per process).

    Maps user_id → WebSocket. One active connection per user (last wins).
    disconnect() requires the caller to pass its own WebSocket so a newer
    connection that already replaced it is never accidentally removed.
    """

    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, ws: WebSocket, user_id: str) -> None:
        await ws.accept()
        self._connections[user_id] = ws
        logger.info("connection_manager.connected", user_id=user_id)

    def disconnect(self, user_id: str, ws: WebSocket) -> None:
        """Remove the connection only if it still belongs to this WebSocket.

        Guards against a race where connection A closes after connection B
        has already taken over the slot — without this check, disconnect()
        would remove B's entry and make the user unreachable.
        """
        if self._connections.get(user_id) is ws:
            self._connections.pop(user_id)
            logger.info("connection_manager.disconnected", user_id=user_id)

    def get_connection(self, user_id: str) -> WebSocket | None:
        return self._connections.get(user_id)

    async def send_to_user(self, user_id: str, message: str) -> None:
        ws = self._connections.get(user_id)
        if ws is None:
            return
        try:
            await ws.send_text(message)
        except Exception:
            logger.warning("connection_manager.send_failed", user_id=user_id)
            self.disconnect(user_id, ws)

    def active_count(self) -> int:
        return len(self._connections)
