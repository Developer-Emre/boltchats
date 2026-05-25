import json

import structlog

from app.managers.broadcast_manager import BroadcastManager
from app.managers.presence_manager import PresenceManager
from app.managers.room_manager import RoomManager
from app.models.ws_event import JoinRoomEvent, LeaveRoomEvent

logger = structlog.get_logger()


async def handle_join_room(
    event: JoinRoomEvent,
    user_id: str,
    room_manager: RoomManager,
    presence_manager: PresenceManager,
    broadcast_manager: BroadcastManager,
) -> None:
    """Add user to room, update presence, and notify other members."""
    room_manager.join(user_id, event.room_id)
    await presence_manager.user_online(user_id, event.room_id)

    notification = json.dumps(
        {"type": "user_joined", "room_id": event.room_id, "user_id": user_id}
    )
    await broadcast_manager.publish(event.room_id, notification)
    logger.info("room_handler.joined", user_id=user_id, room_id=event.room_id)


async def handle_leave_room(
    event: LeaveRoomEvent,
    user_id: str,
    room_manager: RoomManager,
    presence_manager: PresenceManager,
    broadcast_manager: BroadcastManager,
) -> None:
    """Remove user from room, update presence, and notify other members."""
    room_manager.leave(user_id, event.room_id)
    await presence_manager.user_offline_room(user_id, event.room_id)

    notification = json.dumps(
        {"type": "user_left", "room_id": event.room_id, "user_id": user_id}
    )
    await broadcast_manager.publish(event.room_id, notification)
    logger.info("room_handler.left", user_id=user_id, room_id=event.room_id)
