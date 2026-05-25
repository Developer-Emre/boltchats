import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import structlog

from app.managers.broadcast_manager import BroadcastManager
from app.managers.room_manager import RoomManager
from app.models.ws_event import MessageEvent
from app.models.ws_message import OutgoingChatMessage, QueueMessage
from app.utils.message_queue import MessageQueue

logger = structlog.get_logger()


async def handle_message(
    event: MessageEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
    message_queue: MessageQueue,
) -> str | None:
    """Broadcast a chat message and enqueue it for async persistence.

    Returns the serialised OutgoingChatMessage JSON, or None if the user
    is not a member of the target room.
    """
    if not room_manager.is_member(user_id, event.room_id):
        logger.warning("message_handler.not_member", user_id=user_id, room_id=event.room_id)
        return None

    now = datetime.now(timezone.utc)
    message_id = str(uuid4())

    outgoing = OutgoingChatMessage(
        id=message_id,
        room_id=event.room_id,
        sender_id=user_id,
        content=event.content,
        created_at=now.isoformat(),
    )
    queue_msg = QueueMessage(
        room_id=event.room_id,
        sender_id=user_id,
        content=event.content,
        created_at=now,
    )

    outgoing_json = outgoing.model_dump_json()
    await asyncio.gather(
        broadcast_manager.publish(event.room_id, outgoing_json),
        message_queue.enqueue(queue_msg.model_dump_json()),
    )

    logger.info(
        "message_handler.dispatched",
        room_id=event.room_id,
        user_id=user_id,
        message_id=message_id,
    )
    return outgoing_json
