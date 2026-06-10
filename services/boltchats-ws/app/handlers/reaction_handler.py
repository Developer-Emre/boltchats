import structlog

from app.managers.broadcast_manager import BroadcastManager
from app.managers.room_manager import RoomManager
from app.models.ws_event import ReactionAddedEvent, ReactionRemovedEvent
from app.models.ws_message import ReactionAddedBroadcast, ReactionRemovedBroadcast

logger = structlog.get_logger()


async def handle_reaction_added(
    event: ReactionAddedEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
) -> str | None:
    """Broadcast a reaction added to all room members."""
    if not room_manager.is_member(user_id, event.room_id):
        logger.warning(
            "reaction_added_handler.not_member",
            user_id=user_id,
            room_id=event.room_id,
        )
        return None

    outgoing = ReactionAddedBroadcast(
        room_id=event.room_id,
        message_id=event.message_id,
        emoji=event.emoji,
        user_id=event.user_id,
    )
    outgoing_json = outgoing.model_dump_json()
    await broadcast_manager.publish(event.room_id, outgoing_json)

    logger.info(
        "reaction_added_handler.broadcasted",
        room_id=event.room_id,
        user_id=user_id,
        message_id=event.message_id,
        emoji=event.emoji,
    )
    return outgoing_json


async def handle_reaction_removed(
    event: ReactionRemovedEvent,
    user_id: str,
    room_manager: RoomManager,
    broadcast_manager: BroadcastManager,
) -> str | None:
    """Broadcast a reaction removed to all room members."""
    if not room_manager.is_member(user_id, event.room_id):
        logger.warning(
            "reaction_removed_handler.not_member",
            user_id=user_id,
            room_id=event.room_id,
        )
        return None

    outgoing = ReactionRemovedBroadcast(
        room_id=event.room_id,
        message_id=event.message_id,
        emoji=event.emoji,
        user_id=event.user_id,
    )
    outgoing_json = outgoing.model_dump_json()
    await broadcast_manager.publish(event.room_id, outgoing_json)

    logger.info(
        "reaction_removed_handler.broadcasted",
        room_id=event.room_id,
        user_id=user_id,
        message_id=event.message_id,
        emoji=event.emoji,
    )
    return outgoing_json
