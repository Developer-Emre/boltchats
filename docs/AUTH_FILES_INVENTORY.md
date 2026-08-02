# Authentication Files Complete Inventory

This document contains the complete list of all authentication-related files with their roles and locations.

---

## File Structure

```
services/boltchats-api/
├── app/
│   ├── core/
│   │   ├── config.py                    ← Settings (JWT, secrets)
│   │   ├── security.py                  ← Token validation, get_current_user
│   │   ├── database.py                  ← MongoDB connection
│   │   └── redis.py                     ← Redis connection
│   │
│   ├── routers/
│   │   └── auth.py                      ← 6 HTTP endpoints
│   │
│   ├── services/
│   │   ├── __init__.py                  ← Service lazy loading (fixes circular imports)
│   │   └── auth/
│   │       ├── __init__.py
│   │       ├── authentication_service.py ← register(), login()
│   │       ├── token_service.py          ← create_tokens(), verify_access_token(), refresh
│   │       └── password_service.py       ← hash_password(), verify_password()
│   │
│   ├── schemas/
│   │   └── auth.py                      ← Request/response models
│   │
│   ├── models/
│   │   └── identity.py                  ← User, Organization, Member models
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── identity.py                  ← UserRepository, MemberRepository
│   │
│   ├── dependencies.py                  ← Service factories for dependency injection
│   │
│   └── main.py                          ← FastAPI app, import auth router
│
└── tests/
    ├── unit/
    │   └── test_auth_services.py        ← Mocked tests
    └── integration/
        └── test_auth_flow.py            ← Real DB/Redis tests
```

---

## Core Authentication Files (11 total)

### 1. `app/core/config.py` — Settings & Configuration

**Purpose:** Centralized configuration for JWT, database, Redis, CORS

**Key Variables:**
```python
# JWT
secret_key: str                              # Alias: jwt_secret_key
algorithm: str = "HS256"
access_token_expire_minutes: int = 30
refresh_token_expire_days: int = 7

# Database
mongodb_url: str
mongodb_db_name: str = "boltchats"

# Cache
redis_url: str = "redis://localhost:6379/0"

# CORS
cors_origins: list[str] = ["http://localhost:3000"]

# Rate Limiting
rate_limit_requests: int = 1000
rate_limit_window_seconds: int = 60
```

**Usage in Auth:**
- TokenService: reads `jwt_secret_key`, `algorithm`, `access_token_expire_minutes`, `refresh_token_expire_days`
- AuthenticationService: reads `mongodb_db_name`
- Security: reads `jwt_secret_key`, `algorithm`

**Environment Variables Read From:**
- `.env` file in development
- Shell env vars in Docker/K8s

---

### 2. `app/core/security.py` — JWT Validation & Password Hashing

**Purpose:** Token validation, password helpers, FastAPI dependency for auth

**Key Functions:**

```python
def hash_password(plain_password: str) -> str:
    """Hash password using bcrypt"""
    # Used during registration if using this instead of PasswordService

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plaintext password against hash"""
    # Used during login if using this instead of PasswordService

def decode_token(token: str) -> dict:
    """Decode and validate JWT
    - Verifies signature using jwt_secret_key
    - Returns payload dict if valid
    - Raises JWTError if invalid/expired
    """

async def get_current_user(request: Request) -> dict:
    """FastAPI dependency for protected endpoints
    
    Steps:
    1. Extract Bearer token from Authorization header
    2. Decode token using decode_token()
    3. Verify token type == "access" (reject refresh tokens)
    4. Return full payload dict
    
    Raises HTTPException(401) if invalid
    """
```

**Usage Pattern:**
```python
from fastapi import Depends
from app.core.security import get_current_user

@router.get("/protected")
async def protected_endpoint(current_user = Depends(get_current_user)):
    user_id = current_user["user_id"]
    org_id = current_user["org_id"]
    # ...
```

**Token Validation Checklist:**
- ✅ Authorization header present
- ✅ Schema is "Bearer"
- ✅ Token signature valid (matches jwt_secret_key)
- ✅ Token algorithm matches (HS256)
- ✅ Token not expired
- ✅ Token type is "access" (not "refresh")
- ✅ user_id field present

---

### 3. `app/core/database.py` — MongoDB Connection

**Purpose:** Async MongoDB connection via Motor

**Key Functions:**
```python
def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database connection"""
    # Used by UserRepository, MemberRepository, OrganizationRepository
```

**Used By:**
- `AuthenticationService.__init__()` → passes to UserRepository, MemberRepository
- Service factories in `dependencies.py`

---

### 4. `app/core/redis.py` — Redis Connection

**Purpose:** Async Redis connection for token revocation & caching

**Key Functions:**
```python
def get_redis() -> redis.Redis:
    """Get Redis connection"""
    # Used by TokenService for refresh token storage
    # Used by rate limiting middleware
```

**Used By:**
- `TokenService.__init__()` → stores/checks refresh tokens
- Service factories in `dependencies.py`

---

### 5. `app/routers/auth.py` — HTTP Endpoints

**Purpose:** 6 REST endpoints for authentication

**Endpoints:**

| Method | Path | Handler | Body | Returns |
|--------|------|---------|------|---------|
| POST | /auth/register | register() | RegisterRequest | TokenResponse |
| POST | /auth/login | login() | LoginRequest | TokenResponse |
| POST | /auth/refresh | refresh_token() | RefreshTokenRequest | TokenResponse |
| POST | /auth/logout | logout() | — (uses header) | {status: "logged_out"} |
| GET | /auth/me | get_me() | — (uses header) | CurrentUserResponse |
| POST | /auth/health | health_check() | — | HealthResponse |

**Dependencies:**
- Line 5: `from app.core.security import get_current_user as get_current_user_dep`
- Line 6: `from app.dependencies import get_authentication_service, get_token_service`

**Endpoint Details:**

```python
@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
    token_service: TokenService = Depends(get_token_service),
):
    """
    1. auth_service.register(email, password, full_name, org_id="default")
       - Checks email not already registered
       - Hashes password via PasswordService
       - Creates User in MongoDB
       - Creates Organization
       - Creates Member link
       - Returns {user_id, member_id}
    
    2. token_service.create_tokens(user_id, org_id, member_id, roles=[])
       - Creates 15-min access token + 7-day refresh token
       - Stores refresh token in Redis
       - Returns {access_token, refresh_token}
    
    3. Return TokenResponse with tokens
    """

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    """
    1. auth_service.login(email, password)
       - Finds User by email
       - Verifies password using PasswordService.verify_password()
       - Finds Member(s) by user_id
       - Extracts roles from member
       - Returns token_service.create_tokens(...)
    
    2. Return TokenResponse with tokens
    """

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service),
):
    """
    1. token_service.create_access_token_from_refresh(refresh_token, roles=[])
       - Verifies refresh_token signature & expiry
       - Checks Redis for revocation
       - Creates new access token
       - Returns new access_token
    
    2. Return TokenResponse (same refresh token, new access token)
    """

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user_dep),  # Validates access token
    token_service: TokenService = Depends(get_token_service),
):
    """
    1. token_service.revoke_refresh_token(current_user["user_id"])
       - Deletes refresh_token:{user_id} from Redis
       - Future refresh attempts fail
    
    2. Return {status: "logged_out"}
    """

@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    current_user = Depends(get_current_user_dep),  # Validates access token
):
    """
    1. Extract user info from current_user dict
    2. Return CurrentUserResponse
    
    Note: email, full_name empty (not in token, would need DB lookup)
    """

@router.post("/health", response_model=HealthResponse)
async def health_check():
    """
    Simple health check for Kubernetes liveness probe
    Returns: {status: "ok", service: "boltchats-api", timestamp: now}
    """
```

---

### 6. `app/schemas/auth.py` — Request/Response Models

**Purpose:** Pydantic models for input validation and response serialization

**Models:**

```python
class RegisterRequest(BaseModel):
    """POST /auth/register"""
    email: EmailStr                                   # Valid email format
    password: str = Field(..., min_length=8)        # Min 8 characters
    full_name: str = Field(..., min_length=1)
    organization_name: str = Field(..., min_length=1)

class LoginRequest(BaseModel):
    """POST /auth/login"""
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    """POST /auth/refresh"""
    refresh_token: str

class TokenResponse(BaseModel):
    """Response for /register, /login, /refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class LogoutRequest(BaseModel):
    """POST /auth/logout (currently not used in endpoint)"""
    refresh_token: Optional[str] = None

class CurrentUserResponse(BaseModel):
    """GET /auth/me"""
    user_id: str
    email: str              # Currently empty (not in token)
    full_name: str          # Currently empty (not in token)
    organization_id: str
    workspace_id: str       # Currently empty (not in token)
    member_id: str
    roles: list[str]
    permissions: list[str]  # Currently empty (not implemented)

class HealthResponse(BaseModel):
    """POST /auth/health"""
    status: str
    service: str
    version: Optional[str] = None
    timestamp: datetime
```

---

### 7. `app/services/auth/authentication_service.py` — Register & Login Logic

**Purpose:** Business logic for user registration and login

**Class: AuthenticationService**

```python
def __init__(
    self,
    db: AsyncIOMotorDatabase,
    redis_client: redis.Redis,
    token_service: TokenService,
):
    self.users = UserRepository(db)        # Access Users collection
    self.members = MemberRepository(db)    # Access Members collection
    self.token_service = token_service     # Create tokens
    self.password_service = PasswordService()

async def register(
    email: str,
    password: str,
    full_name: str,
    org_id: str,
) -> dict:
    """
    Register new user
    
    Steps:
    1. Check email not already registered
    2. Hash password using bcrypt
    3. Create User document in MongoDB
    4. Create Organization (implicit, not visible here)
    5. Create Member link (user → org)
    6. Log "user_registered" action
    7. Return {user_id, member_id}
    """

async def login(
    email: str,
    password: str,
) -> dict:
    """
    Login user
    
    Steps:
    1. Find User by email (UserRepository.find_by_email)
    2. Verify password (PasswordService.verify_password with bcrypt)
    3. Find Member(s) by user_id (MemberRepository.find_many)
    4. Extract roles from member
    5. Log "user_login" action
    6. Return token_service.create_tokens(user_id, org_id, member_id, roles)
    
    Raises:
    - ConflictError if email already exists (register)
    - UnauthorizedError if password wrong or user not found (login)
    """
```

**Key Notes:**
- Uses `UserRepository.find_by_email()` → returns single user or None
- Uses `MemberRepository.find_many()` → returns list of members (user may be in multiple orgs)
- Role iteration has null-safety check
- Logs all auth events for audit trail

---

### 8. `app/services/auth/token_service.py` — JWT Token Management

**Purpose:** Generate, validate, and revoke JWT tokens

**Class: TokenService**

```python
def __init__(self, redis_client: redis.Redis, settings: Settings):
    self.redis = redis_client      # For refresh token storage
    self.settings = settings       # For jwt_secret_key, algorithm, expiry

async def create_tokens(
    user_id: str,
    org_id: str,
    member_id: str,
    roles: list[str],
) -> dict[str, str]:
    """
    Create access token (15 min) + refresh token (7 days)
    
    Access Token Payload:
    {
      "user_id": user_id,
      "org_id": org_id,
      "member_id": member_id,
      "roles": roles,
      "type": "access",
      "iat": now,
      "exp": now + 15 minutes
    }
    
    Refresh Token Payload:
    {
      "user_id": user_id,
      "org_id": org_id,
      "type": "refresh",
      "iat": now,
      "exp": now + 7 days
    }
    
    Both signed with jwt_secret_key using HS256 algorithm
    
    Refresh token stored in Redis:
      Key: refresh_token:{user_id}
      Value: {refresh_token_string}
      TTL: 7 days
    
    Returns: {access_token, refresh_token}
    """

async def verify_access_token(self, token: str) -> dict:
    """
    Verify access token
    
    Checks:
    - Signature valid (jwt_secret_key)
    - Algorithm HS256
    - Not expired
    - type == "access" (not "refresh")
    - user_id present
    
    Returns: full payload dict
    Raises: jwt.InvalidTokenError if invalid
    """

async def create_access_token_from_refresh(
    self,
    refresh_token: str,
    roles: list[str],
) -> str:
    """
    Create new access token from refresh token
    
    Steps:
    1. Decode refresh_token (verify signature, expiry, type)
    2. Check Redis for revocation: refresh_token:{user_id}
    3. Extract user_id, org_id from refresh token
    4. Create new access token with same org_id, user_id
    5. Return new access_token
    
    Raises: jwt.InvalidTokenError if invalid or revoked
    """

async def revoke_refresh_token(self, user_id: str) -> None:
    """
    Revoke refresh token (logout)
    
    Steps:
    1. Delete Redis key: refresh_token:{user_id}
    2. Future refresh attempts fail (key not found)
    """
```

---

### 9. `app/services/auth/password_service.py` — Password Hashing

**Purpose:** Securely hash and verify passwords using bcrypt

**Class: PasswordService**

```python
@staticmethod
def hash_password(password: str) -> str:
    """
    Hash password using bcrypt via passlib
    
    Features:
    - Adaptive cost factor (increases with computing power)
    - Random salt per password
    - One-way: cannot decrypt
    
    Returns: $2b$12$... (bcrypt format)
    """

@staticmethod
def verify_password(plaintext: str, hashed: str) -> bool:
    """
    Verify plaintext password against hash
    
    Uses constant-time comparison to prevent timing attacks
    
    Returns: True if matches, False otherwise
    """
```

**Algorithm:** Bcrypt (via passlib.context.CryptContext)

---

### 10. `app/dependencies.py` — Service Factories

**Purpose:** Dependency injection factories for FastAPI

**Key Function:**

```python
async def get_authentication_service() -> AsyncGenerator[AuthenticationService, None]:
    """
    FastAPI Depends() factory
    
    Creates AuthenticationService with all dependencies
    Yields to handler, cleans up after
    
    Used in auth.py:
    @router.post("/register")
    async def register(
        auth_service: AuthenticationService = Depends(get_authentication_service)
    ):
    """

async def get_token_service() -> AsyncGenerator[TokenService, None]:
    """
    FastAPI Depends() factory
    
    Creates TokenService with Redis + Settings
    """

# Similar factories for 12+ other services
# (all in one file to avoid circular imports)
```

**Why Needed:**
- Breaks circular import dependency chain
- Provides clean dependency injection for FastAPI
- Allows mocking in tests

---

### 11. `app/models/identity.py` — Domain Models

**Purpose:** MongoDB document schemas for auth

**Classes:**

```python
class User(BaseModel):
    """MongoDB users collection"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    email: str = Field(..., index=True, unique=True)
    password_hash: str
    full_name: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime

class Organization(BaseModel):
    """MongoDB organizations collection"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    owner_id: str
    created_at: datetime

class Member(BaseModel):
    """MongoDB members collection (user-org link)"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    organization_id: str
    user_id: str
    status: MemberStatus = MemberStatus.ACTIVE
    team_ids: list[str] = []
    roles: list[str] = []  # Role IDs
    created_at: datetime
```

**Key Feature:**
- `id` field auto-generates MongoDB ObjectId as string
- Allows Pydantic to work with both JSON (id) and MongoDB (_id)

---

## Supporting Files (Used by Auth)

### `app/repositories/identity.py` — Data Access

```python
class UserRepository:
    async def create(user: User) -> str          # Returns user_id
    async def find_by_email(email: str) -> User  # Returns single user or None
    async def find(id: str) -> User              # Returns single or None
    async def find_many(filter) -> list[User]    # Returns list

class MemberRepository:
    async def create(member: Member) -> str
    async def find_many(filter) -> list[Member]  # Multi-org lookup
    async def find_by_id(id: str) -> Member
```

**Used By:**
- AuthenticationService.register() → creates User, Member
- AuthenticationService.login() → finds User, Member
- Repositories handle all MongoDB operations

---

## Error Handling

### Exceptions (from `services/base.py`)

```python
class BaseServiceError(Exception):
    """Base exception for all service errors"""

class ConflictError(BaseServiceError):
    """Resource already exists"""
    # Raised by: register() if email already exists

class UnauthorizedError(BaseServiceError):
    """User not authorized"""
    # Raised by: login() if password wrong

class NotFoundError(BaseServiceError):
    """Resource not found"""
```

### HTTP Exception Mapping (in routers)

```python
ConflictError → HTTPException(status_code=409)
UnauthorizedError → HTTPException(status_code=401)
JWTError → HTTPException(status_code=401)
Exception → HTTPException(status_code=400)  # Generic fallback
```

---

## Data Flow Diagram

### Registration Flow
```
Client
  ↓ POST /auth/register
Router (auth.py)
  ↓ [get_authentication_service injected]
AuthenticationService.register()
  ├─ UserRepository.find_by_email()  → MongoDB
  ├─ PasswordService.hash_password()  → bcrypt
  ├─ UserRepository.create()          → MongoDB
  ├─ MemberRepository.create()        → MongoDB
  └─ [return {user_id, member_id}]
  ↓ [get_token_service injected]
TokenService.create_tokens()
  ├─ jwt.encode() access token
  ├─ jwt.encode() refresh token
  ├─ Redis.setex(refresh_token:{user_id})  → Redis
  └─ [return {access_token, refresh_token}]
  ↓
Router: TokenResponse
  ↓ 200 OK
Client
```

### Login Flow
```
Client
  ↓ POST /auth/login
Router (auth.py)
  ↓ [get_authentication_service injected]
AuthenticationService.login()
  ├─ UserRepository.find_by_email()  → MongoDB
  ├─ PasswordService.verify_password()  → bcrypt constant-time
  ├─ MemberRepository.find_many()    → MongoDB (all orgs)
  ├─ [extract roles from member]
  └─ [return token_service.create_tokens(...)]
TokenService.create_tokens()
  ├─ jwt.encode() access token
  ├─ jwt.encode() refresh token
  ├─ Redis.setex()  → Redis
  └─ [return tokens]
  ↓
Router: TokenResponse
  ↓ 200 OK
Client
```

### Protected Endpoint Flow
```
Client
  ↓ GET /api/v1/conversations + Authorization: Bearer {access_token}
FastAPI Dependency (security.py:get_current_user)
  ├─ Extract Authorization header
  ├─ Split scheme + token
  ├─ decode_token(token)
  │  ├─ jwt.decode(token, jwt_secret_key)  ← Verify signature
  │  ├─ Check algorithm HS256
  │  ├─ Check not expired
  │  └─ [return payload]
  ├─ Verify type == "access"
  ├─ Verify user_id present
  └─ [return current_user dict]
  ↓ Passed to handler
Route Handler (conversations.py:list_conversations)
  ├─ current_user = {user_id, org_id, member_id, roles, ...}
  ├─ [business logic using current_user info]
  └─ [return response]
  ↓
Client
```

---

## Integration Checklist

To add auth to any endpoint:

```python
from fastapi import Depends
from app.core.security import get_current_user

@router.get("/api/v1/conversations")
async def list_conversations(
    current_user = Depends(get_current_user)  # Adds auth check
):
    user_id = current_user["user_id"]
    org_id = current_user["org_id"]
    member_id = current_user["member_id"]
    roles = current_user["roles"]
    
    # Your business logic here
    return {"conversations": [...]}
```

✅ That's it! The endpoint is now protected.

---

## Summary

| Phase | File | Function |
|-------|------|----------|
| **Setup** | config.py | Read JWT settings, secrets |
| **Request** | security.py | Validate token from header |
| **Register** | auth.py, auth_service.py | Create user, create member, create tokens |
| **Login** | auth.py, auth_service.py | Find user, verify password, create tokens |
| **Token** | token_service.py | Generate JWT with PyJWT |
| **Storage** | token_service.py, redis.py | Store refresh token in Redis |
| **Access** | security.py | Validate access token on protected endpoints |
| **Refresh** | token_service.py | Create new access token from refresh token |
| **Logout** | token_service.py | Revoke refresh token (delete from Redis) |

