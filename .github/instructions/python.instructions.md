---
applyTo: "services/boltchats-{api,ws,storage}/**"
---
# Python Standards — boltchats

## Service Directory Layout
```
app/
├── core/
│   ├── config.py      # Pydantic Settings — reads env vars
│   ├── security.py    # JWT encode/decode + bcrypt
│   ├── database.py    # Motor MongoDB connection
│   └── redis.py       # Redis connection
├── models/            # MongoDB document models
├── schemas/           # Pydantic request/response schemas
├── routers/           # FastAPI routers — NO business logic here
├── services/          # Business logic (one service per router)
├── middlewares/       # auth, rate_limit, logging, cors
├── utils/
│   ├── constants.py   # All constants and enums
│   ├── validators.py
│   └── helpers.py
├── exceptions/
│   ├── http_exceptions.py
│   └── handlers.py
└── main.py            # FastAPI app, lifespan, middleware registration
```

## Mandatory Health Endpoint (every service)
```python
@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}
```

## Idiomatic Patterns
```python
# Comprehension over loop
active = [u for u in users if u.is_active]

# Concurrent independent calls
user, room = await asyncio.gather(
    user_service.get(user_id),
    room_service.get(room_id),
)

# Context managers always
async with motor_client.start_session() as session:
    await collection.insert_one(doc, session=session)

# Specific exception handling
try:
    result = await collection.find_one({"_id": oid})
except PyMongoError as exc:
    raise DatabaseError("Failed to fetch") from exc
```

## Type Hints
```python
# Always: params + return type
async def get_user(user_id: str) -> UserResponse | None: ...

# Built-in generics (Python 3.10+)
def process(items: list[str]) -> dict[str, int]: ...
```

## Style
- PEP 8 · `ruff` / `black` for formatting · `isort` for imports
- Naming: `snake_case` vars/funcs, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- Import order: stdlib → third-party → local (blank line between groups)
- No wildcard imports (`from module import *`)
- No bare `except:` — always catch specific exceptions
