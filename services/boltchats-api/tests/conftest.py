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
def auth_headers() -> dict[str, str]:
    token = create_access_token("test_user_id")
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
