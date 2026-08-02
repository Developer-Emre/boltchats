# Authentication Quick Reference Guide

## Quick Start: Register → Login → Access → Refresh → Logout

### 1. Register New User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "organization_name": "Acme Corp"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

**Response:** Same as register (tokens returned)

---

### 3. Access Protected Endpoint
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response:**
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email": "",
  "full_name": "",
  "organization_id": "default",
  "workspace_id": "",
  "member_id": "507f1f77bcf86cd799439012",
  "roles": ["member"],
  "permissions": []
}
```

---

### 4. Refresh Access Token (when expired)
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<REFRESH_TOKEN>"
  }'
```

**Response:** New access token + same refresh token

---

### 5. Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response:**
```json
{
  "status": "logged_out"
}
```

---

## Token Payload Structure

### Access Token (15 min lifetime)
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "org_id": "default",
  "member_id": "507f1f77bcf86cd799439012",
  "roles": ["member"],
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900
}
```

### Refresh Token (7 day lifetime)
```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "org_id": "default",
  "type": "refresh",
  "iat": 1700000000,
  "exp": 1700604800
}
```

---

## HTTP Status Codes

| Code | Scenario | Endpoint |
|------|----------|----------|
| 200 | Success | All |
| 400 | Bad request (invalid email format, password too short) | `/register`, `/login` |
| 401 | Invalid credentials / Invalid token | `/login`, protected endpoints |
| 409 | Email already registered | `/register` |

---

## File Locations

| File | Purpose |
|------|---------|
| `services/boltchats-api/app/routers/auth.py` | All 6 auth endpoints |
| `services/boltchats-api/app/services/auth/authentication_service.py` | Register/login logic |
| `services/boltchats-api/app/services/auth/token_service.py` | JWT generation/validation |
| `services/boltchats-api/app/core/security.py` | Token validation dependency |
| `services/boltchats-api/app/core/config.py` | JWT settings |

---

## Environment Variables

```bash
JWT_SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=boltchats
REDIS_URL=redis://localhost:6379/0
```

---

## Integration in Your Endpoint

To protect an endpoint, use the `get_current_user` dependency:

```python
from fastapi import Depends
from app.core.security import get_current_user

@router.get("/api/v1/conversations")
async def list_conversations(current_user = Depends(get_current_user)):
    user_id = current_user["user_id"]
    org_id = current_user["org_id"]
    member_id = current_user["member_id"]
    roles = current_user["roles"]
    
    # Your business logic here
    return {"conversations": [...]}
```

---

## Known Limitations

⚠️ **Needs Fixing:**
- Hardcoded `org_id="default"` (no real multi-tenant registration)
- `/me` endpoint returns empty email, full_name, permissions
- Roles empty after token refresh (TODO)
- No rate limiting on login/register
- Access token still valid after logout (until expiry)

---

## Testing

### Swagger UI (Auto-generated)
```
http://localhost:8000/docs
```

### ReDoc (Alternative docs)
```
http://localhost:8000/redoc
```

### OpenAPI Schema
```
http://localhost:8000/openapi.json
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| "Missing authorization header" | No Bearer token | Add `Authorization: Bearer <token>` header |
| "Invalid or expired token" | Token expired or signature mismatch | Login again to get new token |
| "Invalid token type" | Used refresh token instead of access token | Use access token for endpoints |
| "Email already registered" | Account exists | Use different email or login |
| "Invalid credentials" | Wrong password or email | Check email/password |

---

## Debugging

### Check Token Contents
```bash
# Copy your access_token and decode at: https://jwt.io
# Paste token into jwt.io to see payload
```

### Check Redis (refresh token storage)
```bash
redis-cli
> GET refresh_token:{user_id}
```

### Check MongoDB (user document)
```bash
# Use MongoDB Compass or mongosh
db.users.findOne({email: "john@example.com"})
```

### Enable Request Logging
```python
# In main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Next: Protect Your Endpoints

All other API endpoints should use the same `get_current_user` dependency:

```python
@router.get("/api/v1/conversations")
async def list_conversations(current_user = Depends(get_current_user)):
    # current_user is automatically validated
    return {...}
```

The authentication system is now ready to use! 🎉

