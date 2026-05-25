import structlog
from fastapi import WebSocket, WebSocketDisconnect

from app.constants.ws_codes import WsCloseCode
from app.core.config import get_settings
from app.core.security import decode_token

logger = structlog.get_logger()


async def authenticate_ws(ws: WebSocket, token: str | None) -> str:
    """Validate the JWT token for a WebSocket connection.

    On success: returns the authenticated user_id (connection NOT yet accepted).
    On failure: accepts the connection, closes it with code 4001,
                then raises WebSocketDisconnect so the handler exits.
    """
    settings = get_settings()

    if token is None:
        await ws.accept()
        await ws.close(code=WsCloseCode.UNAUTHORIZED)
        raise WebSocketDisconnect(code=WsCloseCode.UNAUTHORIZED)

    try:
        payload = decode_token(token, settings.secret_key, settings.algorithm)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise ValueError("Missing 'sub' claim in token")
        return user_id
    except Exception:
        logger.warning("auth_websocket.unauthorized")
        await ws.accept()
        await ws.close(code=WsCloseCode.UNAUTHORIZED)
        raise WebSocketDisconnect(code=WsCloseCode.UNAUTHORIZED)
