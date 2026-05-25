"""Unit tests for room_service — all external deps mocked."""

import pytest
from bson import ObjectId
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.exceptions.http_exceptions import (
    ForbiddenException,
    NotFoundException,
)
from app.schemas.room_schema import CreateRoomRequest
from app.services import room_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _room_doc(
    room_id: ObjectId | None = None,
    owner_id: str = "owner1",
    member_ids: list[str] | None = None,
) -> dict:
    oid = room_id or ObjectId()
    return {
        "_id": oid,
        "name": "General",
        "description": "A room",
        "owner_id": owner_id,
        "member_ids": member_ids if member_ids is not None else [owner_id],
        "is_private": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def _make_collection(
    find_one_return=None,
    insert_one_id: ObjectId | None = None,
    find_one_and_update_return=None,
    find_return: list | None = None,
    update_one_return=None,
) -> MagicMock:
    ins_result = MagicMock()
    ins_result.inserted_id = insert_one_id or ObjectId()

    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)
    collection.insert_one = AsyncMock(return_value=ins_result)
    collection.find_one_and_update = AsyncMock(return_value=find_one_and_update_return)
    collection.update_one = AsyncMock(return_value=update_one_return)

    # .find().sort().limit().to_list() chain
    cursor_mock = MagicMock()
    cursor_mock.sort.return_value = cursor_mock
    cursor_mock.limit.return_value = cursor_mock
    cursor_mock.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor_mock)

    return collection


def _make_db(collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_room_success() -> None:
    new_id = ObjectId()
    collection = _make_collection(insert_one_id=new_id)
    db = _make_db(collection)
    payload = CreateRoomRequest(name="General", description="Hello", is_private=False)

    result = await room_service.create(payload, "owner1", db)

    assert result.id == str(new_id)
    assert result.name == "General"
    assert result.owner_id == "owner1"
    assert "owner1" in result.member_ids
    collection.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_create_room_name_too_short_raises() -> None:
    with pytest.raises(Exception):
        CreateRoomRequest(name="")


# ---------------------------------------------------------------------------
# list_rooms
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_rooms_empty() -> None:
    collection = _make_collection(find_return=[])
    db = _make_db(collection)

    result = await room_service.list_rooms(db)

    assert result.items == []
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_list_rooms_has_next_cursor() -> None:
    docs = [_room_doc() for _ in range(21)]
    collection = _make_collection(find_return=docs)
    db = _make_db(collection)

    result = await room_service.list_rooms(db, limit=20)

    assert len(result.items) == 20
    assert result.next_cursor == str(docs[19]["_id"])


@pytest.mark.asyncio
async def test_list_rooms_no_next_cursor_when_fewer_than_limit() -> None:
    docs = [_room_doc() for _ in range(5)]
    collection = _make_collection(find_return=docs)
    db = _make_db(collection)

    result = await room_service.list_rooms(db, limit=20)

    assert len(result.items) == 5
    assert result.next_cursor is None


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_room_by_id_success() -> None:
    room_id = ObjectId()
    collection = _make_collection(find_one_return=_room_doc(room_id))
    db = _make_db(collection)

    result = await room_service.get_by_id(str(room_id), db)

    assert result.id == str(room_id)


@pytest.mark.asyncio
async def test_get_room_by_id_not_found_raises() -> None:
    collection = _make_collection(find_one_return=None)
    db = _make_db(collection)

    with pytest.raises(NotFoundException):
        await room_service.get_by_id(str(ObjectId()), db)


@pytest.mark.asyncio
async def test_get_room_by_id_invalid_id_raises() -> None:
    collection = _make_collection()
    db = _make_db(collection)

    with pytest.raises(NotFoundException):
        await room_service.get_by_id("bad-id", db)


# ---------------------------------------------------------------------------
# join
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_join_room_success() -> None:
    room_id = ObjectId()
    updated_doc = _room_doc(room_id, member_ids=["owner1", "user2"])
    collection = _make_collection(find_one_and_update_return=updated_doc)
    db = _make_db(collection)

    result = await room_service.join(str(room_id), "user2", db)

    assert "user2" in result.member_ids


@pytest.mark.asyncio
async def test_join_room_already_member_is_idempotent() -> None:
    room_id = ObjectId()
    existing = _room_doc(room_id, member_ids=["owner1", "user2"])
    # find_one_and_update returns None (already member), find_one returns existing
    collection = _make_collection(
        find_one_and_update_return=None, find_one_return=existing
    )
    db = _make_db(collection)

    result = await room_service.join(str(room_id), "user2", db)

    assert "user2" in result.member_ids


@pytest.mark.asyncio
async def test_join_room_not_found_raises() -> None:
    collection = _make_collection(
        find_one_and_update_return=None, find_one_return=None
    )
    db = _make_db(collection)

    with pytest.raises(NotFoundException):
        await room_service.join(str(ObjectId()), "user2", db)


# ---------------------------------------------------------------------------
# leave
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_leave_room_success() -> None:
    room_id = ObjectId()
    doc = _room_doc(room_id, owner_id="owner1", member_ids=["owner1", "user2"])
    collection = _make_collection(find_one_return=doc)
    db = _make_db(collection)

    await room_service.leave(str(room_id), "user2", db)

    collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_leave_room_owner_raises_forbidden() -> None:
    room_id = ObjectId()
    doc = _room_doc(room_id, owner_id="owner1")
    collection = _make_collection(find_one_return=doc)
    db = _make_db(collection)

    with pytest.raises(ForbiddenException):
        await room_service.leave(str(room_id), "owner1", db)


@pytest.mark.asyncio
async def test_leave_room_not_found_raises() -> None:
    collection = _make_collection(find_one_return=None)
    db = _make_db(collection)

    with pytest.raises(NotFoundException):
        await room_service.leave(str(ObjectId()), "user2", db)
