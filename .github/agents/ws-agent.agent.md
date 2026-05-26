---
name: ws-agent
description: "Use when working on boltchats-ws: WebSocket connections, real-time messaging, Redis Pub/Sub broadcast between instances, Redis Queue (LPUSH) for message persistence, connection manager, presence manager, rate limiting for WS."
tools: [read, edit, search, execute, web]
---

# WebSocket Agent — boltchats-ws

You are working exclusively on the `services/boltchats-ws/` service.

## Scope
- WebSocket connection lifecycle (connect, receive, disconnect)
- Real-time message broadcast across multiple pod instances
- Queueing messages for async persistence (Write-Behind pattern)
- Online user presence tracking

## Key Files
```
services/boltchats-ws/app/
├── managers/
│   ├── connection_manager.py  ← Active WebSocket connections (in-memory)
│   ├── broadcast_manager.py   ← Redis PUBLISH/SUBSCRIBE — broadcast only
│   └── presence_manager.py    ← Redis Set — online user tracking
└── utils/
    └── message_queue.py       ← Redis LPUSH — write to persistence queue
```

## Redis Rules — Critical
| File | Redis command | Purpose |
|------|--------------|---------|
| `broadcast_manager.py` | PUBLISH / SUBSCRIBE | Real-time multi-instance broadcast |
| `message_queue.py` | LPUSH only | Hand off to storage service |
| `presence_manager.py` | SADD / SREM / SMEMBERS | Online user set |

**NEVER** use LPUSH in `broadcast_manager.py`.
**NEVER** use PUBLISH in `message_queue.py`.
These two patterns must remain completely separate.

## Write-Behind Flow
```
User sends message
  ↓
ws receives via WebSocket
  ↓ (simultaneously)
  ├── PUBLISH to Redis channel  → other ws instances → User B sees it instantly
  └── LPUSH to Redis queue      → boltchats-storage → MongoDB (async, no wait)
```

## Load for deeper context
- Redis patterns: `#file:.github/instructions/redis.instructions.md`
- Python patterns: `#file:.github/instructions/python.instructions.md`
- Security rules: `#file:.github/instructions/security.instructions.md`

## Tool Usage Rules
- Read each file at most twice — re-reading the same file a third time is forbidden
- If grep_search returns sufficient results, do not follow up with file_search
- Do not re-read a file after making changes to verify — trust the edit
- Complete the plan in 5 tool calls or fewer; if more are needed, stop and ask the user