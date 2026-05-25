import json

import structlog
from fastapi import WebSocket

logger = structlog.get_logger()


async def handle_ping(ws: WebSocket) -> None:
    """Respond to a client ping with a pong."""
    await ws.send_text(json.dumps({"type": "pong"}))
    logger.debug("ping_handler.pong_sent")
