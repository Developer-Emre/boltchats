import structlog
from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from app.exceptions.http_exceptions import DatabaseException, NotFoundException
from app.schemas.user_schema import UpdateUserRequest, UserResponse
from app.utils.constants import Collection, ErrorMessage
from app.utils.helpers import parse_object_id

logger = structlog.get_logger()


def _doc_to_user(doc: dict) -> UserResponse:
    return UserResponse(
        id=str(doc["_id"]),
        username=doc["username"],
        email=doc["email"],
        is_active=doc.get("is_active", True),
    )


async def get_me(user_id: str, db) -> UserResponse:
    oid = parse_object_id(user_id, ErrorMessage.USER_NOT_FOUND)
    try:
        doc = await db[Collection.USERS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query user") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.USER_NOT_FOUND)
    return _doc_to_user(doc)


async def update_me(user_id: str, payload: UpdateUserRequest, db) -> UserResponse:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return await get_me(user_id, db)

    oid = parse_object_id(user_id, ErrorMessage.USER_NOT_FOUND)
    try:
        doc = await db[Collection.USERS].find_one_and_update(
            {"_id": oid},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
    except PyMongoError as exc:
        raise DatabaseException("Failed to update user") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.USER_NOT_FOUND)

    await logger.ainfo("user_updated", user_id=user_id)
    return _doc_to_user(doc)


async def get_by_id(target_id: str, db) -> UserResponse:
    oid = parse_object_id(target_id, ErrorMessage.USER_NOT_FOUND)
    try:
        doc = await db[Collection.USERS].find_one({"_id": oid})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query user") from exc

    if not doc:
        raise NotFoundException(ErrorMessage.USER_NOT_FOUND)
    return _doc_to_user(doc)
