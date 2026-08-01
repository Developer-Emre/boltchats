import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
from httpx import ASGITransport, AsyncClient

from app.core.database import get_database
from app.core.redis import get_redis
from app.core.security import create_access_token
from app.main import app


@pytest.fixture
def mock_collection() -> MagicMock:
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.insert_one = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.find = AsyncMock()
    return collection


@pytest.fixture
def mock_db(mock_collection: MagicMock) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=mock_collection)
    return db


@pytest_asyncio.fixture
async def mock_redis():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.aclose()


@pytest.fixture
def auth_headers(user_id: str = "test-user-123") -> dict[str, str]:
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client(mock_db: MagicMock, mock_redis):
    app.dependency_overrides[get_database] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


# Test data fixtures
@pytest.fixture
def org_id() -> str:
    return "test-org-123"


@pytest.fixture
def user_id() -> str:
    return "test-user-456"


@pytest.fixture
def member_id() -> str:
    return "test-member-789"


@pytest.fixture
def customer_id() -> str:
    return "test-customer-111"


@pytest.fixture
def conversation_id() -> str:
    return "test-conversation-222"


@pytest.fixture
def message_id() -> str:
    return "test-message-333"


@pytest.fixture
def test_org_data(org_id: str) -> dict:
    return {
        "id": org_id,
        "name": "Test Organization",
        "slug": "test-org",
        "member_count": 0,
        "workspace_count": 0,
    }


@pytest.fixture
def test_user_data(user_id: str) -> dict:
    return {
        "id": user_id,
        "email": "test@example.com",
        "password_hash": "$2b$12$...",
        "full_name": "Test User",
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def test_member_data(org_id: str, user_id: str, member_id: str) -> dict:
    return {
        "id": member_id,
        "organization_id": org_id,
        "workspace_id": "test-workspace-101",
        "user_id": user_id,
        "email": "test@example.com",
        "full_name": "Test User",
        "status": "active",
        "roles": [],
        "team_ids": [],
    }


@pytest.fixture
def test_customer_data(org_id: str, customer_id: str) -> dict:
    return {
        "id": customer_id,
        "organization_id": org_id,
        "name": "John Doe",
        "email": "customer@example.com",
        "phone": "+1234567890",
        "conversation_count": 1,
        "message_count": 5,
        "last_contact_at": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def test_conversation_data(org_id: str, customer_id: str, conversation_id: str) -> dict:
    return {
        "id": conversation_id,
        "organization_id": org_id,
        "customer_id": customer_id,
        "channel": "email",
        "subject": "Test conversation",
        "status": "open",
        "assigned_to": None,
        "last_message_id": None,
        "last_message_at": None,
        "message_count": 0,
        "participant_count": 0,
        "labels": [],
    }


@pytest.fixture
def test_message_data(conversation_id: str, customer_id: str, message_id: str) -> dict:
    return {
        "id": message_id,
        "conversation_id": conversation_id,
        "sender_id": customer_id,
        "text": "Hello, this is a test message",
        "message_type": "text",
        "reply_to_message_id": None,
        "edited_at": None,
        "edited_by": None,
        "deleted_at": None,
        "deleted_by": None,
        "metadata": {},
    }

