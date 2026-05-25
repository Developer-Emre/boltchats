"""Unit tests for user_service — all external deps mocked."""

import pytest
from bson import ObjectId
from unittest.mock import AsyncMock, MagicMock

from pymongo import ReturnDocument

from app.exceptions.http_exceptions import NotFoundException
from app.schemas.user_schema import UpdateUserRequest
from app.services import user_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user_doc(user_id: ObjectId | None = None, username: str = "alice") -> dict:
    oid = user_id or ObjectId()
    return {
        "_id": oid,
        "username": username,
        "email": f"{username}@example.com",
        "is_active": True,
    }


def _make_db(
    find_one_return=None,
    find_one_and_update_return=None,
) -> MagicMock:
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)
    collection.find_one_and_update = AsyncMock(
        return_value=find_one_and_update_return
    )
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=collection)
    return db


# ---------------------------------------------------------------------------
# get_me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_me_success() -> None:
    user_id = ObjectId()
    db = _make_db(find_one_return=_user_doc(user_id))

    result = await user_service.get_me(str(user_id), db)

    assert result.id == str(user_id)
    assert result.username == "alice"
    assert result.email == "alice@example.com"


@pytest.mark.asyncio
async def test_get_me_not_found_raises() -> None:
    db = _make_db(find_one_return=None)

    with pytest.raises(NotFoundException):
        await user_service.get_me(str(ObjectId()), db)


@pytest.mark.asyncio
async def test_get_me_invalid_id_raises() -> None:
    db = _make_db()

    with pytest.raises(NotFoundException):
        await user_service.get_me("not-a-valid-id", db)


# ---------------------------------------------------------------------------
# update_me
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_me_success() -> None:
    user_id = ObjectId()
    updated_doc = _user_doc(user_id, username="alice_new")
    db = _make_db(find_one_and_update_return=updated_doc)
    payload = UpdateUserRequest(username="alice_new")

    result = await user_service.update_me(str(user_id), payload, db)

    assert result.username == "alice_new"


@pytest.mark.asyncio
async def test_update_me_no_fields_returns_current_profile() -> None:
    user_id = ObjectId()
    db = _make_db(find_one_return=_user_doc(user_id))
    payload = UpdateUserRequest()  # all None

    result = await user_service.update_me(str(user_id), payload, db)

    assert result.id == str(user_id)


@pytest.mark.asyncio
async def test_update_me_user_not_found_raises() -> None:
    db = _make_db(find_one_and_update_return=None)
    payload = UpdateUserRequest(username="ghost")

    with pytest.raises(NotFoundException):
        await user_service.update_me(str(ObjectId()), payload, db)


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_success() -> None:
    user_id = ObjectId()
    db = _make_db(find_one_return=_user_doc(user_id))

    result = await user_service.get_by_id(str(user_id), db)

    assert result.id == str(user_id)


@pytest.mark.asyncio
async def test_get_by_id_not_found_raises() -> None:
    db = _make_db(find_one_return=None)

    with pytest.raises(NotFoundException):
        await user_service.get_by_id(str(ObjectId()), db)


@pytest.mark.asyncio
async def test_get_by_id_invalid_id_raises() -> None:
    db = _make_db()

    with pytest.raises(NotFoundException):
        await user_service.get_by_id("totally-invalid", db)
