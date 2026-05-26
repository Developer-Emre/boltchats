# GitHub Copilot Instructions — boltchats

## Services
- `boltchats-api` :8000 · `boltchats-ws` :8001 · `boltchats-storage` (async worker) · `boltchats-web` :3000
- No `shared/` folder — ever. Every service deploys independently.
- Inter-service communication: REST | Redis Pub/Sub | Redis Queue

## Absolute Rules
- `async`/`await` everywhere — no blocking I/O
- No hardcoded values → `core/config.py` (Pydantic Settings)
- No magic numbers/strings → `utils/constants.py` or enums
- No `print()` → use `structlog`
- Full type hints on every function (params + return type)
- Router never contains business logic → delegate to service layer
- Each service owns its own `core/security.py` — JWT validated independently

## Redis — Two Patterns, Never Mixed
- **Pub/Sub** (broadcast): `broadcast_manager.py` only — PUBLISH/SUBSCRIBE
- **Queue** (persistence): `message_queue.py` (LPUSH) → `consumer.py` (BRPOP)

## Before Any Change
1. List affected files
2. Explain the plan
3. Wait for **"proceed"**

---

## Context Files — Load When Needed
| Working on… | Load this file |
|-------------|----------------|
| Python service code | `#file:.github/instructions/python.instructions.md` |
| Redis / queue / pub-sub | `#file:.github/instructions/redis.instructions.md` |
| Tests | `#file:.github/instructions/testing.instructions.md` |
| Kubernetes / Terraform / CI-CD | `#file:.github/instructions/infra.instructions.md` |
| Next.js / TypeScript | `#file:.github/instructions/frontend.instructions.md` |
| Security / JWT / auth | `#file:.github/instructions/security.instructions.md` |
