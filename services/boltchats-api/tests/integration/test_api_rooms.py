"""Integration tests — Rooms + Users + Messages HTTP layer via ASGI client."""

import pytest
import pytest_asyncio
from bson import ObjectId
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient

from app.core.database import get_database
from app.core.redis import get_redis
from app.core.security import create_access_token
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

USER_ID = str(ObjectId())
ROOM_ID = ObjectId()


def _auth_headers(user_id: str = USER_ID) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def _user_doc(user_id: str = USER_ID) -> dict:
    return {
        "_id": ObjectId(user_id),
        "username": "alice",
        "email": "alice@example.com",
        "is_active": True,
    }


def _room_doc(
    room_id: ObjectId = ROOM_ID,
    owner_id: str = USER_ID,
    member_ids: list[str] | None = None,
) -> dict:
    return {
        "_id": room_id,
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
) -> MagicMock:
    ins = MagicMock()
    ins.inserted_id = insert_one_id or ObjectId()

    col = MagicMock()
    col.find_one = AsyncMock(return_value=find_one_return)
    col.insert_one = AsyncMock(return_value=ins)
    col.find_one_and_update = AsyncMock(return_value=find_one_and_update_return)
    col.update_one = AsyncMock()

    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.to_list = AsyncMock(return_value=find_return or [])
    col.find = MagicMock(return_value=cursor)

    return col


@pytest_asyncio.fixture
async def redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def api(redis):
    """ASGI client with a single collection mock (overridden per-test via db fixture)."""
    col = _make_collection()
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=col)

    app.dependency_overrides[get_database] = lambda: db
    app.dependency_overrides[get_redis] = lambda: redis
    app.state.redis = redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac, db
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_me_success(api) -> None:
    ac, db = api
    col = _make_collection(find_one_return=_user_doc())
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get("/users/me", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_me_unauthenticated(api) -> None:
    ac, _ = api
    resp = await ac.get("/users/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no token


@pytest.mark.asyncio
@pytest.mark.integration
async def test_patch_me_success(api) -> None:
    ac, db = api
    updated = _user_doc()
    updated["username"] = "alice_v2"
    col = _make_collection(find_one_and_update_return=updated)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.patch(
        "/users/me",
        headers=_auth_headers(),
        json={"username": "alice_v2"},
    )

    assert resp.status_code == 200
    assert resp.json()["username"] == "alice_v2"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_user_by_id_not_found(api) -> None:
    ac, db = api
    col = _make_collection(find_one_return=None)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get(
        f"/users/{ObjectId()}", headers=_auth_headers()
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Rooms — create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_room_returns_201(api) -> None:
    ac, db = api
    new_id = ObjectId()
    col = _make_collection(insert_one_id=new_id)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.post(
        "/rooms",
        headers=_auth_headers(),
        json={"name": "General", "description": "Hello"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "General"
    assert body["id"] == str(new_id)
    assert USER_ID in body["member_ids"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_room_unauthenticated(api) -> None:
    ac, _ = api
    resp = await ac.post("/rooms", json={"name": "General"})
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_room_name_too_short_returns_422(api) -> None:
    ac, _ = api
    resp = await ac.post("/rooms", headers=_auth_headers(), json={"name": ""})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Rooms — list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_rooms_empty(api) -> None:
    ac, db = api
    col = _make_collection(find_return=[])
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get("/rooms", headers=_auth_headers())

    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["next_cursor"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_rooms_returns_items(api) -> None:
    ac, db = api
    docs = [_room_doc(ObjectId()) for _ in range(3)]
    col = _make_collection(find_return=docs)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get("/rooms", headers=_auth_headers())

    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 3


# ---------------------------------------------------------------------------
# Rooms — get by id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_room_success(api) -> None:
    ac, db = api
    col = _make_collection(find_one_return=_room_doc(ROOM_ID))
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get(f"/rooms/{ROOM_ID}", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["id"] == str(ROOM_ID)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_room_not_found(api) -> None:
    ac, db = api
    col = _make_collection(find_one_return=None)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get(f"/rooms/{ObjectId()}", headers=_auth_headers())

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Rooms — join
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_join_room_success(api) -> None:
    ac, db = api
    other_user = str(ObjectId())
    updated = _room_doc(ROOM_ID, member_ids=[USER_ID, other_user])
    col = _make_collection(find_one_and_update_return=updated)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.post(f"/rooms/{ROOM_ID}/join", headers=_auth_headers(other_user))

    assert resp.status_code == 200
    assert other_user in resp.json()["member_ids"]


# ---------------------------------------------------------------------------
# Rooms — leave
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_leave_room_success(api) -> None:
    ac, db = api
    other_user = str(ObjectId())
    doc = _room_doc(ROOM_ID, owner_id=USER_ID, member_ids=[USER_ID, other_user])
    col = _make_collection(find_one_return=doc)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.delete(
        f"/rooms/{ROOM_ID}/leave", headers=_auth_headers(other_user)
    )

    assert resp.status_code == 204


@pytest.mark.asyncio
@pytest.mark.integration
async def test_leave_room_as_owner_returns_403(api) -> None:
    ac, db = api
    doc = _room_doc(ROOM_ID, owner_id=USER_ID)
    col = _make_collection(find_one_return=doc)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.delete(f"/rooms/{ROOM_ID}/leave", headers=_auth_headers())

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Messages — history
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_messages_room_not_found(api) -> None:
    ac, db = api
    col = _make_collection(find_one_return=None)
    db.__getitem__ = MagicMock(return_value=col)

    resp = await ac.get(
        f"/rooms/{ObjectId()}/messages", headers=_auth_headers()
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_messages_empty_history(api) -> None:
    ac, db = api

    # We need two collections: rooms (find_one → room doc) + messages (find → [])
    # Both use db[collection_name], so we intercept with a smart mock
    room_col = _make_collection(find_one_return=_room_doc(ROOM_ID))
    msg_col = _make_collection(find_return=[])

    def _get_col(name: str):
        return room_col if name == "rooms" else msg_col

    db.__getitem__ = MagicMock(side_effect=_get_col)

    resp = await ac.get(f"/rooms/{ROOM_ID}/messages", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["items"] == []
    assert resp.json()["next_cursor"] is None
