---
applyTo: "services/**/tests/**"
---
# Testing Standards — boltchats

## Layout (identical across all 3 Python services)
```
tests/
├── unit/          # MongoDB + Redis mocked — zero external deps
├── integration/   # Real MongoDB + Redis instances
└── conftest.py    # Shared fixtures
```

## Every Test File Must Cover
1. **Happy path** — successful scenario
2. **Error case** — expected failure (bad input, DB error, auth fail)
3. **Edge case** — boundary condition (empty list, max length, concurrent access)

## TDD Default
Tests are written **before** the feature. No feature PR without tests.

## Unit Test Pattern
```python
# Mock external dependencies
@pytest.mark.asyncio
async def test_create_message_success(mock_db, mock_redis):
    # Arrange
    payload = MessagePayload(room_id="r1", content="hi", sender_id="u1")
    mock_db.insert_one.return_value = InsertOneResult(...)

    # Act
    result = await message_service.create(payload)

    # Assert
    assert result.room_id == "r1"
    mock_db.insert_one.assert_called_once()
```

## Integration Test Pattern
```python
# Real DB — use fixtures that clean up after
@pytest.mark.asyncio
@pytest.mark.integration
async def test_message_persisted(real_db, real_redis):
    ...
    # Always clean up: use yield fixtures or explicit teardown
```

## conftest.py Must Provide
- `mock_db` — Motor collection mock
- `mock_redis` — Redis mock (aioredis)
- `real_db` — Motor client to test MongoDB instance
- `real_redis` — Redis client to test Redis instance
- `auth_headers` — valid JWT headers for authenticated routes
