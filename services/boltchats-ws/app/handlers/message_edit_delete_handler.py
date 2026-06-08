import structlog

from app.managers.broadcast_manager import BroadcastManager
from app.managers.room_manager import RoomManager
from app.models.ws_event import MessageDeletedEvent, MessageEditedEvent
from app.models.ws_message import MessageDeletedBroadcast, MessageEditedBroadcast

logger = structlog.get_logger()


async def handle_message_edited(
    event: MessageEditedEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
) -> str | None:
    """Broadcast a message edit to all room members.

    The edit was already persisted by the API. We just relay it to the room
    so all connected clients see the change in real time.
    """
    if not room_manager.is_member(user_id, event.room_id):
        logger.warning(
            "message_edit_handler.not_member",
            user_id=user_id,
            room_id=event.room_id,
        )
        return None

    outgoing = MessageEditedBroadcast(
        room_id=event.room_id,
        message_id=event.message_id,
        content=event.content,
        edited_at=event.edited_at,
    )
    outgoing_json = outgoing.model_dump_json()
    await broadcast_manager.publish(event.room_id, outgoing_json)

    logger.info(
        "message_edit_handler.broadcasted",
        room_id=event.room_id,
        user_id=user_id,
        message_id=event.message_id,
    )
    return outgoing_json


async def handle_message_deleted(
    event: MessageDeletedEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
) -> str | None:
    """Broadcast a message deletion to all room members.

    The deletion was already persisted by the API. We just relay it to the room
    so all connected clients see the change in real time.
    """
    if not room_manager.is_member(user_id, event.room_id):
        logger.warning(
            "message_delete_handler.not_member",
            user_id=user_id,
            room_id=event.room_id,
        )
        return None

    outgoing = MessageDeletedBroadcast(
        room_id=event.room_id,
        message_id=event.message_id,
    )
    outgoing_json = outgoing.model_dump_json()
    await broadcast_manager.publish(event.room_id, outgoing_json)

    logger.info(
        "message_delete_handler.broadcasted",
        room_id=event.room_id,
        user_id=user_id,
        message_id=event.message_id,
    )
    return outgoing_json
