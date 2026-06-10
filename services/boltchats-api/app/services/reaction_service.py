import structlog
from datetime import datetime, timezone
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import DatabaseException, ForbiddenException, NotFoundException
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id
from app.schemas.reaction_schema import ReactionData

logger = structlog.get_logger()


async def add_reaction(
    room_id: str,
    message_id: str,
    user_id: str,
    emoji: str,
    db,
) -> ReactionData:
    """Add a reaction to a message. If user already reacted with this emoji, do nothing."""
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    message_oid = parse_object_id(message_id, ErrorMessage.INVALID_ID)

    # Verify room exists and user is member
    try:
        room = await db[Collection.ROOMS].find_one({"_id": room_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not room:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    if user_id not in room.get("member_ids", []):
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    # Verify message exists and not deleted
    try:
        message = await db[Collection.MESSAGES].find_one({"_id": message_oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch message") from exc

    if not message:
        raise NotFoundException("Message not found")

    if message.get("deleted_at"):
        raise NotFoundException("Cannot react to deleted message")

    # Upsert reaction
    try:
        reaction = await db[Collection.REACTIONS].find_one_and_update(
            {
                "message_id": message_oid,
                "room_id": room_oid,
                "emoji": emoji,
            },
            {
                "$addToSet": {"users": user_id},
                "$setOnInsert": {
                    "message_id": message_oid,
                    "room_id": room_oid,
                    "emoji": emoji,
                    "created_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
            return_document=True,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to add reaction") from exc

    return ReactionData(emoji=emoji, users=reaction.get("users", []))


async def remove_reaction(
    room_id: str,
    message_id: str,
    user_id: str,
    emoji: str,
    db,
) -> None:
    """Remove a reaction from a message. If user didn't react, do nothing."""
    room_oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    message_oid = parse_object_id(message_id, ErrorMessage.INVALID_ID)

    try:
        result = await db[Collection.REACTIONS].update_one(
            {
                "message_id": message_oid,
                "room_id": room_oid,
                "emoji": emoji,
            },
            {"$pull": {"users": user_id}},
        )

        # Delete reaction if no users left
        if result.modified_count > 0:
            reaction = await db[Collection.REACTIONS].find_one(
                {
                    "message_id": message_oid,
                    "room_id": room_oid,
                    "emoji": emoji,
                }
            )
            if reaction and not reaction.get("users"):
                await db[Collection.REACTIONS].delete_one(
                    {
                        "message_id": message_oid,
                        "room_id": room_oid,
                        "emoji": emoji,
                    }
                )
    except PyMongoError as exc:
        raise DatabaseException("Failed to remove reaction") from exc


async def get_message_reactions(
    message_id: str,
    db,
) -> list[ReactionData]:
    """Get all reactions for a message."""
    message_oid = parse_object_id(message_id, ErrorMessage.INVALID_ID)

    try:
        reactions = await db[Collection.REACTIONS].find(
            {"message_id": message_oid}
        ).to_list(None)
    except PyMongoError as exc:
        raise DatabaseException("Failed to fetch reactions") from exc

    return [
        ReactionData(emoji=r["emoji"], users=r.get("users", []))
        for r in reactions
    ]
