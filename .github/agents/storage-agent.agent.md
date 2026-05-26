---
name: storage-agent
description: "Use when working on boltchats-storage: Redis BRPOP consumer loop, async MongoDB persistence, Write-Behind pattern, message worker, dead-letter handling, retry logic."
tools: [read, edit, search, execute, web]
---

# Storage Agent — boltchats-storage

You are working exclusively on the `services/boltchats-storage/` service.

## Scope
- Async worker — no HTTP server, no REST endpoints (except `/health`)
- Continuously reads messages from Redis Queue via BRPOP
- Persists messages to MongoDB via Motor

## Key Files
```
services/boltchats-storage/app/
├── consumer.py      ← BRPOP loop — reads from Redis queue, writes to MongoDB
├── core/config.py   ← REDIS_QUEUE_NAME comes from here (never hardcoded)
├── core/database.py ← Motor MongoDB connection
└── core/redis.py    ← Redis connection (aioredis)
```

## Consumer Loop Pattern
```python
async def consume() -> None:
    while True:
        # BRPOP blocks until a message arrives — no busy-waiting
        raw = await redis.brpop(settings.REDIS_QUEUE_NAME, timeout=0)
        if raw is None:
            continue
        payload = MessagePayload.model_validate_json(raw[1])
        await message_repo.insert(payload)
```

## Rules
- `BRPOP` is used **only** in `consumer.py` — nowhere else
- Queue name is always read from `settings.REDIS_QUEUE_NAME` (constants)
- On MongoDB write failure: log with structlog, implement retry with exponential backoff
- Never use `SUBSCRIBE` here — this service does not use Pub/Sub

## Tool Usage Rules
- Read each file at most twice — re-reading the same file a third time is forbidden
- If grep_search returns sufficient results, do not follow up with file_search
- Do not re-read a file after making changes to verify — trust the edit
- Complete the plan in 5 tool calls or fewer; if more are needed, stop and ask the user

## Load for deeper context
- Redis patterns: `#file:.github/instructions/redis.instructions.md`
- Python patterns: `#file:.github/instructions/python.instructions.md`
- Testing: `#file:.github/instructions/testing.instructions.md`
