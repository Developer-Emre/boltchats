import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import structlog

from app.managers.broadcast_manager import BroadcastManager
from app.managers.connection_manager import ConnectionManager
from app.managers.room_manager import RoomManager
from app.models.ws_event import MessageEvent
from app.models.ws_message import MessageConfirmed, OutgoingChatMessage, QueueMessage
from app.utils.message_queue import MessageQueue

logger = structlog.get_logger()


async def handle_message(
    event: MessageEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
    message_queue: MessageQueue,
    connection_manager: ConnectionManager,
) -> str | None:
    """Broadcast a chat message and enqueue it for async persistence.

    Two-phase delivery:
    1. Clean broadcast → Redis pub/sub → every room member (no CID).
    2. Direct receipt  → connection_manager → sender only (contains CID so
       the client can replace its optimistic placeholder by exact id match).

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
        id=message_id,
        room_id=event.room_id,
        sender_id=user_id,
        content=event.content,
        created_at=now,
    )

    outgoing_json = outgoing.model_dump_json()

    tasks: list = [
        broadcast_manager.publish(event.room_id, outgoing_json),
        message_queue.enqueue(queue_msg.model_dump_json()),
    ]

    # Send a private delivery receipt to the sender so it can swap its
    # optimistic placeholder. This is never published to the room channel.
    if event.client_message_id:
        confirmed = MessageConfirmed(
            client_message_id=event.client_message_id,
            server_id=message_id,
        )
        tasks.append(connection_manager.send_to_user(user_id, confirmed.model_dump_json()))

    await asyncio.gather(*tasks)

    logger.info(
        "message_handler.dispatched",
        room_id=event.room_id,
        user_id=user_id,
        message_id=message_id,
    )
    return outgoing_json
