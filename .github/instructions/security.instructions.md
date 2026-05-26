---
applyTo: "services/**/core/**,services/**/middlewares/**"
---
# Security Rules — boltchats

## JWT
- Secret read from `.env` → never hardcoded
- Each service has its own `core/security.py` — no shared JWT lib
- Token validation happens independently in every service

## Passwords
- Hashed with `bcrypt` before storage
- Plaintext passwords → **forbidden** anywhere in codebase

## Input Validation
- All user input validated with Pydantic before use
- Never trust raw request data in service or router layer

## CORS
- Origins read from `CORS_ORIGINS` env var in `core/config.py`
- Never hardcode allowed origins

## Rate Limiting
- Applied in every service via Redis counter
- Location: `middlewares/rate_limit.py` in each service

## Secrets Management
- Kubernetes: Sealed Secret or External Secret (Vault/AWS SSM)
- Never write secrets to ConfigMap
- `.env` files never committed — `.env.example` only

## Refresh Tokens
- Stored in Redis with prefix `REDIS_PREFIX_REFRESH_TOKEN` (from constants)
- TTL enforced at storage time
