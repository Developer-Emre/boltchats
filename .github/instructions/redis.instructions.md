---
applyTo: "services/boltchats-ws/app/managers/**,services/boltchats-ws/app/utils/**,services/boltchats-storage/app/**"
---
# Redis Patterns — boltchats

## Two Patterns — Never Mix

### Pattern A: Real-Time Broadcast (Pub/Sub)
```
boltchats-ws (inst 1) → PUBLISH → Redis → SUBSCRIBE → boltchats-ws (inst 2)
```
- File: `services/boltchats-ws/app/managers/broadcast_manager.py` ONLY
- Messages can be lost (fire-and-forget)
- **PUBLISH / SUBSCRIBE used ONLY in this file**

### Pattern B: Persistence Queue (List)
```
boltchats-ws → LPUSH → Redis → BRPOP → boltchats-storage → MongoDB
```
- Writer: `services/boltchats-ws/app/utils/message_queue.py` ONLY
- Reader: `services/boltchats-storage/app/consumer.py` ONLY
- Messages must NOT be lost
- **LPUSH / BRPOP used ONLY in these two files**

## Other Redis Usages
| Purpose | Location | Key prefix |
|---------|----------|------------|
| Rate limit counter | `middlewares/rate_limit.py` | from constants |
| Refresh token storage | `core/security.py` | `REDIS_PREFIX_REFRESH_TOKEN` |
| Presence (online users) | `managers/presence_manager.py` | Redis Set |

## Connection
- Redis client: `core/redis.py` in each service that needs it
- Config: read from env vars via `core/config.py`
- Never instantiate Redis client outside `core/redis.py`
