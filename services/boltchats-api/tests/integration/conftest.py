"""
Integration test configuration

Sets up real MongoDB and Redis for integration testing
"""

import pytest
import asyncio
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.config import Settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Load test settings"""
    return Settings(
        environment="test",
        mongodb_url="mongodb://localhost:27017",
        redis_url="redis://localhost:6379/0",
        database_name="boltchats_test",
    )


@pytest.fixture(scope="session")
async def mongodb_client(settings: Settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Connect to MongoDB for testing"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    yield client
    # Cleanup: drop test database
    await client.drop_database(settings.database_name)
    client.close()


@pytest.fixture(scope="session")
async def mongodb(
    mongodb_client: AsyncIOMotorClient,
    settings: Settings,
) -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get test database"""
    db = mongodb_client[settings.database_name]
    yield db


@pytest.fixture(scope="session")
async def redis_client(settings: Settings) -> AsyncGenerator[Redis, None]:
    """Connect to Redis for testing"""
    redis = await Redis.from_url(settings.redis_url, decode_responses=True)
    yield redis
    # Cleanup: flush test database
    await redis.flushdb()
    await redis.close()


@pytest.fixture(autouse=True)
async def cleanup_mongodb(mongodb: AsyncIOMotorDatabase):
    """Clean up collections after each test"""
    yield
    # Drop all collections after each test
    async for collection_name in mongodb.list_collection_names():
        if not collection_name.startswith("system."):
            await mongodb[collection_name].drop()


@pytest.fixture(autouse=True)
async def cleanup_redis(redis_client: Redis):
    """Clean up Redis after each test"""
    yield
    await redis_client.flushdb()


@pytest.fixture
async def org_id() -> str:
    """Test organization ID"""
    return "org-integration-test-123"


@pytest.fixture
async def member_id() -> str:
    """Test member ID"""
    return "member-integration-test-123"


@pytest.fixture
async def workspace_id() -> str:
    """Test workspace ID"""
    return "workspace-integration-test-123"


@pytest.fixture
async def customer_id() -> str:
    """Test customer ID"""
    return "customer-integration-test-123"


@pytest.fixture
async def conversation_id() -> str:
    """Test conversation ID"""
    return "conversation-integration-test-123"


@pytest.fixture
async def message_id() -> str:
    """Test message ID"""
    return "message-integration-test-123"
