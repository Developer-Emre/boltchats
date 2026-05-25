from datetime import datetime, timezone

import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import (
    DatabaseException,
    ForbiddenException,
    NotFoundException,
)
from app.schemas.room_schema import CreateRoomRequest, RoomListResponse, RoomResponse
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()

_DEFAULT_LIMIT: int = 20
_MAX_LIMIT: int = 100


def _doc_to_room(doc: dict) -> RoomResponse:
    return RoomResponse(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description", ""),
        owner_id=doc["owner_id"],
        member_ids=doc.get("member_ids", []),
        is_private=doc.get("is_private", False),
        created_at=doc["created_at"],
    )


async def create(payload: CreateRoomRequest, owner_id: str, db) -> RoomResponse:
    now = datetime.now(timezone.utc)
    doc = {
        "name": payload.name,
        "description": payload.description,
        "owner_id": owner_id,
        "member_ids": [owner_id],
        "is_private": payload.is_private,
        "created_at": now,
        "updated_at": now,
    }
    try:
        result = await db[Collection.ROOMS].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create room") from exc

    doc["_id"] = result.inserted_id
    await logger.ainfo("room_created", room_id=str(result.inserted_id), owner_id=owner_id)
    return _doc_to_room(doc)


async def list_rooms(
    db, cursor: str | None = None, limit: int = _DEFAULT_LIMIT
) -> RoomListResponse:
    limit = min(limit, _MAX_LIMIT)
    query: dict = {}
    if cursor:
        cursor_oid = parse_object_id(cursor, ErrorMessage.INVALID_ID)
        query["_id"] = {"$gt": cursor_oid}

    try:
        docs = (
            await db[Collection.ROOMS]
            .find(query)
            .sort("_id", 1)
            .limit(limit + 1)
            .to_list(limit + 1)
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to list rooms") from exc

    has_more = len(docs) > limit
    items = [_doc_to_room(d) for d in docs[:limit]]
    next_cursor = str(docs[limit - 1]["_id"]) if has_more else None
    return RoomListResponse(items=items, next_cursor=next_cursor)


async def get_by_id(room_id: str, db) -> RoomResponse:
    oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    try:
        doc = await db[Collection.ROOMS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)
    return _doc_to_room(doc)


async def join(room_id: str, user_id: str, db) -> RoomResponse:
    oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    try:
        doc = await db[Collection.ROOMS].find_one_and_update(
            {"_id": oid, "member_ids": {"$ne": user_id}},
            {
                "$push": {"member_ids": user_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to join room") from exc

    if doc:
        await logger.ainfo("room_joined", room_id=room_id, user_id=user_id)
        return _doc_to_room(doc)

    # No update: either room missing or already a member — distinguish
    try:
        existing = await db[Collection.ROOMS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not existing:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)
    return _doc_to_room(existing)  # already a member — idempotent


async def leave(room_id: str, user_id: str, db) -> None:
    oid = parse_object_id(room_id, ErrorMessage.ROOM_NOT_FOUND)
    try:
        doc = await db[Collection.ROOMS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query room") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.ROOM_NOT_FOUND)

    if doc["owner_id"] == user_id:
        raise ForbiddenException(ErrorMessage.OWNER_CANNOT_LEAVE)

    try:
        await db[Collection.ROOMS].update_one(
            {"_id": oid},
            {
                "$pull": {"member_ids": user_id},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to leave room") from exc

    await logger.ainfo("room_left", room_id=room_id, user_id=user_id)
