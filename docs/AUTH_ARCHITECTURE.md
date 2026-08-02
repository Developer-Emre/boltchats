# Authentication Architecture Documentation

## Overview

This document describes the complete authentication system in boltchats-api, including all components, data flows, token lifecycle, and security measures.

---

## 1. Authentication Files Inventory

### Core Files (9 total)

| File | Role | Key Responsibility |
|------|------|-------------------|
| `app/core/config.py` | Configuration | JWT secrets, algorithm, token expiry times |
| `app/core/security.py` | Security Layer | Token validation, password hashing, get_current_user dependency |
| `app/core/database.py` | Database | MongoDB connection via Motor (async) |
| `app/core/redis.py` | Cache | Redis connection for token revocation |
| `app/routers/auth.py` | HTTP Endpoints | /register, /login, /logout, /refresh, /me, /health |
| `app/schemas/auth.py` | Data Validation | Request/response Pydantic models |
| `app/services/auth/authentication_service.py` | Business Logic | User registration and login flows |
| `app/services/auth/token_service.py` | Token Management | JWT creation, validation, refresh, revocation |
| `app/services/auth/password_service.py` | Password Hashing | Bcrypt password hashing/verification |
| `app/dependencies.py` | Dependency Injection | Service factory functions for FastAPI |
| `app/models/identity.py` | Domain Models | User, Organization, Member entities |

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Client (Web/Mobile)                  │
└──────────────┬────────────────────────────────────────────────┘
               │
    ┌──────────▼──────────┐
    │  FastAPI Router     │
    │ /auth/*             │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────────────────────────────────┐
    │  Endpoint Handlers (auth.py)                     │
    │  ├─ POST /register → register(RegisterRequest)  │
    │  ├─ POST /login → login(LoginRequest)           │
    │  ├─ POST /refresh → refresh_token(...)          │
    │  ├─ POST /logout → logout(current_user)         │
    │  ├─ GET /me → get_me(current_user)              │
    │  └─ POST /health → health_check()               │
    └──────────┬──────────────────────────────────────┘
               │
    ┌──────────▼─────────────────────────────┐
    │ Service Layer (Business Logic)          │
    │                                         │
    │  ┌─────────────────────────────────┐   │
    │  │ AuthenticationService           │   │
    │  │ ├─ register()                   │   │
    │  │ ├─ login()                      │   │
    │  │ └─ [uses TokenService & repos]  │   │
    │  └─────────────────────────────────┘   │
    │                                         │
    │  ┌─────────────────────────────────┐   │
    │  │ TokenService                    │   │
    │  │ ├─ create_tokens()              │   │
    │  │ ├─ verify_access_token()        │   │
    │  │ ├─ create_access_token_from_... │   │
    │  │ ├─ revoke_refresh_token()       │   │
    │  │ └─ [uses JWT + Redis]           │   │
    │  └─────────────────────────────────┘   │
    │                                         │
    │  ┌─────────────────────────────────┐   │
    │  │ PasswordService                 │   │
    │  │ ├─ hash_password()              │   │
    │  │ └─ verify_password()            │   │
    │  └─────────────────────────────────┘   │
    │                                         │
    └──────────┬─────────────────────────────┘
               │
    ┌──────────▼──────────┬────────────────┐
    │                     │                │
    ▼                     ▼                ▼
 ┌─────────┐        ┌──────────┐      ┌───────┐
 │ MongoDB │        │  Redis   │      │ JWT   │
 │ Users   │        │ Refresh  │      │Token  │
 │ Members │        │ Tokens   │      │Lib    │
 │ Roles   │        │ Revoke   │      └───────┘
 │ Orgs    │        │ Keys     │
 └─────────┘        └──────────┘
```

---

## 3. Complete Authentication Flow

### 3.1 Registration Flow

```
POST /auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_name": "Acme Corp"
}
```

**Steps:**

1. **Endpoint** (auth.py:register)
   - Receives RegisterRequest
   - Injects AuthenticationService & TokenService

2. **AuthenticationService.register()**
   - Check if email already exists (UserRepository.find_by_email)
   - Hash password using PasswordService.hash_password (bcrypt)
   - Create User document in MongoDB
   - Create Organization with default settings
   - Create Member link (user_id → organization_id)
   - Log action "user_registered"
   - Return {user_id, member_id}

3. **TokenService.create_tokens()**
   - Generate access token (15 min expiry, type="access")
   - Generate refresh token (7 day expiry, type="refresh")
   - Store refresh token in Redis with key: `refresh_token:{user_id}`
   - Return {access_token, refresh_token}

4. **Response**
   ```json
   {
     "access_token": "eyJ0eXAi...",
     "refresh_token": "eyJ0eXAi...",
     "token_type": "bearer",
     "expires_in": 900
   }
   ```

**Error Cases:**
- Email already registered → ConflictError
- Password too weak → ValidationError (min 8 chars)
- Invalid email format → ValidationError

---

### 3.2 Login Flow

```
POST /auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Steps:**

1. **Endpoint** (auth.py:login)
   - Receives LoginRequest
   - Injects AuthenticationService

2. **AuthenticationService.login()**
   - Find User by email (UserRepository.find_by_email)
   - Verify password with PasswordService.verify_password (bcrypt constant-time)
   - If password invalid → raise UnauthorizedError
   - Find Member(s) by user_id using find_many()
   - Extract roles from member_roles (iterate safely with null-checks)
   - Log action "user_login"
   - Call TokenService.create_tokens with roles list

3. **TokenService.create_tokens()**
   - Same as registration step 3

4. **Response**
   ```json
   {
     "access_token": "eyJ0eXAi...",
     "refresh_token": "eyJ0eXAi...",
     "token_type": "bearer",
     "expires_in": 900
   }
   ```

**Error Cases:**
- User not found → 401 Invalid credentials
- Wrong password → 401 Invalid credentials (intentionally vague for security)
- Member not found → 401 Invalid credentials

---

### 3.3 Access Protected Endpoint

```
GET /api/v1/conversations
Headers:
  Authorization: Bearer eyJ0eXAi...
```

**Steps:**

1. **FastAPI Dependency** (security.py:get_current_user)
   - Extract bearer token from Authorization header
   - Call decode_token(token)
   - Verify token signature using jwt_secret_key
   - Check token type == "access" (reject refresh tokens)
   - Verify not expired
   - Return full payload dict: {user_id, org_id, member_id, roles, type, iat, exp}

2. **Endpoint Handler**
   - Receives current_user as dict
   - Access current_user["user_id"], current_user["org_id"], etc.
   - Continue with business logic

**Error Cases:**
- No Authorization header → 401 Missing authorization header
- Invalid scheme (not Bearer) → 401 Invalid or expired token
- Token signature invalid → 401 Invalid or expired token
- Token expired → 401 Invalid or expired token
- Token type != "access" → 401 Invalid or expired token
- Token missing user_id → 401 Invalid or expired token

---

### 3.4 Refresh Token Flow

```
POST /auth/refresh
{
  "refresh_token": "eyJ0eXAi..."
}
```

**Steps:**

1. **Endpoint** (auth.py:refresh_token)
   - Receives RefreshTokenRequest
   - Injects TokenService

2. **TokenService.create_access_token_from_refresh()**
   - Decode refresh token (validate signature, type, expiry)
   - Check Redis for revocation: `refresh_token:{user_id}` still exists?
   - If revoked → raise UnauthorizedError
   - Extract user_id, org_id from payload
   - Create new access token (same org_id, user_id, but empty roles TODO)
   - Return new access_token

3. **Response**
   ```json
   {
     "access_token": "eyJ0eXAi...",
     "refresh_token": "eyJ0eXAi...",
     "token_type": "bearer",
     "expires_in": 900
   }
   ```

**Error Cases:**
- Refresh token invalid/expired → 401 Invalid refresh token
- Refresh token revoked → 401 Invalid refresh token
- Refresh token signature mismatch → 401 Invalid refresh token

---

### 3.5 Logout Flow

```
POST /auth/logout
Headers:
  Authorization: Bearer eyJ0eXAi...
```

**Steps:**

1. **Endpoint** (auth.py:logout)
   - Receives current_user from dependency (validates access token)
   - Injects TokenService

2. **TokenService.revoke_refresh_token(user_id)**
   - Delete Redis key: `refresh_token:{user_id}`
   - Future refresh attempts → key not found → 401

3. **Response**
   ```json
   {
     "status": "logged_out"
   }
   ```

**Notes:**
- Access token remains valid until expiry (stateless JWT)
- For immediate logout, implement token blacklist or short-lived access tokens
- Refresh token becomes useless immediately (Redis key deleted)

---

### 3.6 Get Current User

```
GET /auth/me
Headers:
  Authorization: Bearer eyJ0eXAi...
```

**Steps:**

1. **Endpoint** (auth.py:get_me)
   - Receives current_user from dependency

2. **Return CurrentUserResponse**
   - user_id: from token
   - org_id: from token
   - member_id: from token
   - roles: from token
   - email, full_name, permissions: NOT in token, return empty strings (TODO)

**Limitations:**
- Email and full_name not stored in JWT (too large)
- Would require DB lookup or store minimal info (email only)
- Permissions empty; would need PermissionService

---

## 4. Token Structure

### Access Token Payload

```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "org_id": "default",
  "member_id": "507f1f77bcf86cd799439012",
  "roles": ["member"],
  "type": "access",
  "iat": 1700000000,
  "exp": 1700000900,
  "iss": null,
  "aud": null
}
```

**Fields:**
- `user_id`: MongoDB user document ID
- `org_id`: Organization the member belongs to
- `member_id`: MongoDB member document ID (user's record in that org)
- `roles`: List of role IDs (e.g., ["member"], ["admin", "moderator"])
- `type`: Always "access" (distinguishes from refresh token)
- `iat`: Issued at (Unix timestamp)
- `exp`: Expires at (Unix timestamp)

**Lifetime:** 15 minutes (configured in settings.access_token_expire_minutes)

### Refresh Token Payload

```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "org_id": "default",
  "type": "refresh",
  "iat": 1700000000,
  "exp": 1700604800,
  "iss": null,
  "aud": null
}
```

**Fields:**
- Similar to access token, but no roles or member_id
- `type`: Always "refresh"

**Lifetime:** 7 days (configured in settings.refresh_token_expire_days)

**Storage:** Also stored in Redis key `refresh_token:{user_id}` for revocation tracking

---

## 5. Security Implementation Details

### 5.1 Password Hashing

**File:** `app/services/auth/password_service.py`

**Algorithm:** Bcrypt (via passlib)

**Key Properties:**
- Adaptive: cost factor increases with Moore's Law
- Salted: each hash includes random salt
- Constant-time comparison: prevents timing attacks
- One-way: no decryption, only verification

**Usage:**
```python
# Registration/password change
hashed = password_service.hash_password("PlaintextPassword")

# Login verification
is_valid = password_service.verify_password("PlaintextPassword", hashed)
```

### 5.2 JWT Security

**Algorithm:** HS256 (HMAC-SHA256, symmetric)

**Secret Key:** 
- Environment variable: `JWT_SECRET_KEY` or `SECRET_KEY`
- Default (dev only): "change-me-to-a-strong-random-secret"
- Production: Must be 32+ random bytes, rotated periodically

**Token Validation Checklist:**
1. ✅ Signature valid (matches secret key)
2. ✅ Algorithm matches (HS256)
3. ✅ Expiry time not passed
4. ✅ Token type correct ("access" for endpoints, "refresh" for refresh flow)
5. ✅ Required fields present (user_id)

### 5.3 Refresh Token Revocation

**Method:** Redis-backed revocation

**Storage:** 
```
Key: refresh_token:{user_id}
Value: {refresh_token_string}
TTL: 7 days
```

**Logout Process:**
1. Delete Redis key → refresh token immediately invalid
2. Access token remains valid until expiry (grace period)
3. For immediate access denial, use token blacklist (not implemented)

### 5.4 Rate Limiting

**Currently Not Implemented on Auth Endpoints**

**TODO:** Add rate limiting to prevent brute force:
- `/auth/login` → 5 attempts per 15 minutes per IP
- `/auth/register` → 1 registration per email per day
- `/auth/refresh` → 10 refreshes per minute per user

**Implementation:** Use Redis counter with Middleware

### 5.5 Error Handling

**Intentional Vagueness (Security):**
```python
# GOOD - does not leak user existence
raise HTTPException(
    status_code=401,
    detail="Invalid credentials"
)

# BAD - leaks if email exists
raise HTTPException(
    status_code=400,
    detail="Email already registered"
)
```

**Current Issues:**
- ❌ Register endpoint returns raw exception detail (reveals implementation)
- ❌ Traceback print in login handler (visible in logs)
- ✅ Login uses generic "Invalid credentials" (good)

---

## 6. Configuration

### 6.1 Environment Variables

**File:** `app/core/config.py`

```python
# JWT
JWT_SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=boltchats

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW_SECONDS=60
```

### 6.2 Development vs Production

| Setting | Dev | Prod |
|---------|-----|------|
| JWT_SECRET_KEY | any string | 32+ random bytes |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | 15-30 |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | 7-30 |
| RATE_LIMIT_REQUESTS | 1000 | 100 |
| RATE_LIMIT_WINDOW_SECONDS | 60 | 60 |
| CORS_ORIGINS | ["http://localhost:3000"] | ["https://app.example.com"] |

---

## 7. Data Models

### User Model

**File:** `app/models/identity.py`

```python
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))  # MongoDB _id
    email: str  # unique
    password_hash: str  # bcrypt hash
    full_name: str
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Organization Model

```python
class Organization(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    owner_id: str  # User who created it
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Member Model

```python
class Member(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    organization_id: str  # Org this member belongs to
    user_id: str  # User reference
    status: MemberStatus = MemberStatus.ACTIVE
    team_ids: list[str] = []
    roles: list[str] = []  # Role IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## 8. Dependency Injection

### Service Factories

**File:** `app/dependencies.py`

FastAPI uses async generators to provide services:

```python
async def get_authentication_service() -> AsyncGenerator[AuthenticationService, None]:
    """Provides AuthenticationService instance"""
    from app.core.config import settings
    db = get_database()
    redis = get_redis()
    token_service = TokenService(redis, settings)
    service = AuthenticationService(db, redis, token_service)
    yield service
```

**Usage in Routes:**
```python
@router.post("/register")
async def register(
    payload: RegisterRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    result = await auth_service.register(...)
```

### Why Lazy Loading?

Original code had circular imports:
```
main.py → error_handlers → services.__init__ → auth → token_service → models.integration → services (cycle!)
```

**Solution:** PEP 562 `__getattr__` in services/__init__.py

```python
def __getattr__(name: str):
    """Lazy load service classes on access"""
    if name == "AuthenticationService":
        from .auth import AuthenticationService
        return AuthenticationService
    # ... more services
```

---

## 9. Known Issues & TODOs

### Critical
- [ ] Hardcoded `org_id="default"` → no real multi-tenant registration
- [ ] `/me` endpoint returns empty email/full_name/permissions
- [ ] Roles empty on token refresh → roles lost after refresh
- [ ] No rate limiting on `/login`, `/register` endpoints

### Security
- [ ] No email verification flow
- [ ] Access token remains valid after logout (until expiry)
- [ ] Register endpoint leaks exception details
- [ ] Traceback printed in login handler (visible in logs)
- [ ] No CSRF protection
- [ ] No password strength validation (min 8 chars only)

### Future
- [ ] Implement permission service
- [ ] Add two-factor authentication
- [ ] Implement token blacklist for immediate access denial
- [ ] Add audit logging for auth events
- [ ] Implement refresh token rotation
- [ ] Add IP-based rate limiting
- [ ] Implement OAuth2 integration (Google, GitHub, etc.)

---

## 10. Testing Guide

### Unit Tests (Mocked)

```python
@pytest.mark.asyncio
async def test_register_success(auth_service_mock):
    """Test successful registration"""
    result = await auth_service_mock.register(
        email="test@example.com",
        password="SecurePassword123",
        full_name="Test User",
        org_id="test-org"
    )
    
    assert result["user_id"]
    assert result["member_id"]
```

### Integration Tests (Real DB)

```python
@pytest.mark.asyncio
async def test_login_flow(mongodb, redis):
    """Test complete login flow"""
    # 1. Register
    result = await auth_service.register(...)
    
    # 2. Login
    tokens = await auth_service.login(...)
    
    # 3. Verify token in Redis
    refresh_key = f"refresh_token:{result['user_id']}"
    stored_token = await redis.get(refresh_key)
    assert stored_token == tokens["refresh_token"]
```

### Manual Testing (cURL)

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123",
    "full_name": "John Doe",
    "organization_name": "Acme Corp"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123"
  }'

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Refresh token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<REFRESH_TOKEN>"
  }'

# Logout
curl -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## 11. Deployment Considerations

### Secret Management
- **Dev:** Use `.env` file (gitignored)
- **Staging:** Use environment variables (from CI/CD secrets)
- **Production:** Use secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

### Token Rotation
- Periodically change JWT_SECRET_KEY
- Support key versioning (decode with old keys, encode with new key)
- Implement key rotation window (7-14 days)

### Monitoring & Alerts
- Track failed login attempts (403 rate)
- Alert on unusual token validation failures
- Monitor password hash operation time (indicates DoS)
- Track registration spike (indicates bot attack)

### Compliance
- GDPR: Right to deletion (delete user + related tokens/sessions)
- CCPA: Data access, portability
- HIPAA/SOC2: Audit logging of auth events

---

## Conclusion

The boltchats authentication system is built on industry-standard practices:
- **JWT** for stateless token-based auth
- **Bcrypt** for secure password hashing  
- **Redis** for stateful refresh token management
- **Async/await** for non-blocking operations
- **Dependency injection** for testability and loose coupling

Next steps: Implement fixes for known issues, add rate limiting, implement permission system, and add comprehensive audit logging.

