import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
from mongomock_motor import AsyncMongoMockClient


@pytest_asyncio.fixture
async def mock_db():
    client = AsyncMongoMockClient()
    db = client["boltchats_test"]
    yield db
    client.close()


@pytest_asyncio.fixture
async def mock_redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture
def mock_collection():
    col = MagicMock()
    col.insert_one = AsyncMock()
    return col
