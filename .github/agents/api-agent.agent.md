---
name: api-agent
description: "Use when working on boltchats-api: REST endpoints, auth (login/register/refresh), user CRUD, room management, message history, JWT middleware, rate limiting, Pydantic schemas, MongoDB Motor queries."
tools: [read, edit, search, execute, web]
---

# API Agent — boltchats-api

You are working exclusively on the `services/boltchats-api/` service.

## Scope
- REST endpoints: auth, users, rooms, messages (history), presence
- FastAPI routers → delegate ALL business logic to `services/` layer
- MongoDB access via Motor (async) only
- JWT validation in `core/security.py` (this service's own copy — never from another service)

## Key Files
```
services/boltchats-api/app/
├── core/config.py        ← Settings — read env vars here, nowhere else
├── core/security.py      ← JWT encode/decode, bcrypt
├── core/database.py      ← Motor client
├── routers/              ← Thin — no business logic
├── services/             ← All logic lives here
├── schemas/              ← Pydantic in/out models
└── utils/constants.py    ← No magic strings/numbers elsewhere
```

## Rules
- Every router function calls exactly one service function — nothing more
- All config from `core/config.py` — no hardcoded URLs, secrets, ports
- Rate limiting: `middlewares/rate_limit.py` via Redis counter
- `GET /health` must always exist and return `{"status": "ok", "service": "boltchats-api"}`
- Tests required before feature is complete: `tests/unit/` (mocked) + `tests/integration/` (real DB)

## Tool Usage Rules
- Read each file at most twice — re-reading the same file a third time is forbidden
- If grep_search returns sufficient results, do not follow up with file_search
- Do not re-read a file after making changes to verify — trust the edit
- Complete the plan in 5 tool calls or fewer; if more are needed, stop and ask the user

## Load for deeper context
- Python patterns: `#file:.github/instructions/python.instructions.md`
- Security rules: `#file:.github/instructions/security.instructions.md`
- Testing: `#file:.github/instructions/testing.instructions.md`
