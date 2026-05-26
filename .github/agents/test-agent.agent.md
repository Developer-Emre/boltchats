---
name: test-agent
description: "Use when writing or reviewing tests: unit tests with mocked dependencies, integration tests with real MongoDB and Redis, pytest fixtures in conftest.py, TDD workflow, test coverage, async test patterns with pytest-asyncio."
tools: [read, edit, search, execute, web]
---

# Test Agent — boltchats

You are working on test code across all Python services.

## Scope
- Unit tests: all external dependencies mocked (MongoDB, Redis)
- Integration tests: real MongoDB + Redis instances
- `conftest.py`: shared fixtures for each service
- TDD: tests written before or alongside feature code

## Test Layout (identical across all 3 Python services)
```
tests/
├── unit/
│   ├── test_<router_name>.py   ← router/service logic, mocked DB + Redis
│   └── test_<util_name>.py
├── integration/
│   └── test_<feature>.py       ← real DB, marked @pytest.mark.integration
└── conftest.py                 ← all fixtures here
```

## Every Test File Must Contain
1. **Happy path** — the normal successful scenario
2. **Error case** — expected failure (auth error, validation error, DB error)
3. **Edge case** — boundary conditions (empty input, max values, concurrency)

## Required conftest.py Fixtures
```python
@pytest.fixture
def mock_db() -> AsyncMock:          # Motor collection mock

@pytest.fixture
def mock_redis() -> AsyncMock:       # aioredis mock

@pytest.fixture
async def real_db() -> AsyncGenerator:    # real Motor client → yield → cleanup

@pytest.fixture
async def real_redis() -> AsyncGenerator: # real Redis client → yield → cleanup

@pytest.fixture
def auth_headers() -> dict[str, str]:     # valid JWT Authorization header
```

## Async Test Pattern
```python
@pytest.mark.asyncio
async def test_create_message_success(mock_db: AsyncMock, mock_redis: AsyncMock) -> None:
    # Arrange
    payload = MessagePayload(room_id="r1", content="hello", sender_id="u1")
    mock_db.insert_one.return_value = InsertOneResult(inserted_id=ObjectId(), acknowledged=True)

    # Act
    result = await message_service.create(payload, db=mock_db)

    # Assert
    assert result.room_id == "r1"
    mock_db.insert_one.assert_called_once()
```

## Rules
- No magic strings in assertions — use constants from `utils/constants.py`
- Integration tests must always clean up after themselves (yield fixtures)
- Mark integration tests: `@pytest.mark.integration`
- No `time.sleep()` in tests — use `asyncio.sleep()` or mock timers

## Load for deeper context
- Testing standards: `#file:.github/instructions/testing.instructions.md`
- Python patterns: `#file:.github/instructions/python.instructions.md`
