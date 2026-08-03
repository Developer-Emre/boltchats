# Authentication Flow — Dosya Haritası

**Version:** 1.0  
**Last Updated:** 2026-08-03  
**Purpose:** Tüm authentication files'ını ve data flow'unu anlamak

---

## 📊 Flow Özeti

```
HTTP Request
    ↓
Router (app/routers/auth.py)
    ↓
Service (app/services/auth/*.py)
    ↓
Repository (app/repositories/identity.py)
    ↓
MongoDB Collection
```

---

## 🔐 CORE — Configuration & Security

### `app/core/config.py`
**Amaç:** Tüm settings ve environment variables  
**Auth-related settings:**
```python
jwt_secret_key: str  # JWT imzası için
algorithm: str = "HS256"  # Token encoding
access_token_expire_minutes: int = 30  # Access token TTL
refresh_token_expire_days: int = 7  # Refresh token TTL
email_verification_token_expire_minutes: int = 1440  # 24 hours
frontend_url: str  # Email verification link'i için
```

**Ne Yapılır:**
- Env var'ları okur (`.env` dosyasından)
- Validation yapar (Pydantic Settings)
- Tüm diğer servisler buradan config alır

**Used by:**
- `token_service.py` — token expiry times
- `security.py` — JWT secret key
- `routers/auth.py` — email links

---

### `app/core/security.py`
**Amaç:** JWT token handling ve user authentication  

**Functions:**
```python
decode_token(token: str) → dict
    ├─ JWT'yi config'ten gelen secret ile decode ediyor
    ├─ JWTError varsa ValueError fırlatıyor
    └─ Payload dict return ediyor

get_current_user(request: Request) → dict
    ├─ Authorization header'ından Bearer token çıkartıyor
    ├─ decode_token() ile doğruluyor
    ├─ Token type = "access" kontrolü yapıyor
    └─ Full payload dict return ediyor (user_id, org_id, member_id, roles, etc)

create_access_token(user_id, org_id, member_id, roles, expires_in_minutes) → str
    ├─ Test fixtures için token generate ediyor (production: TokenService kulllanıyor)
    └─ JWT string return ediyor
```

**Used by:**
- `routers/auth.py` — `/me` endpoint'te `get_current_user` dependency
- `tests/conftest.py` — test tokens generate etmek

---

### `app/core/database.py`
**Amaç:** MongoDB connection management  
**Functions:**
- `get_database()` → Motor AsyncIOMotorDatabase

**Used by:**
- Dependency injection (all services)

---

### `app/core/redis.py`
**Amaç:** Redis connection management  
**Functions:**
- `get_redis()` → redis.asyncio.Redis

**Used by:**
- TokenService (refresh tokens, rate limiting)
- Dependency injection

---

## 📦 DEPENDENCIES — Injection Layer

### `app/dependencies.py`
**Amaç:** Service instances inject etmek  

**Functions:**
```python
async def get_authentication_service() → AuthenticationService
    └─ db + redis + token_service ile initialize

async def get_token_service() → TokenService
    └─ redis + settings ile initialize

async def get_password_service() → PasswordService
async def get_role_service() → RoleService
async def get_label_service() → LabelService
```

**Flow:**
```python
@router.post("/login")
async def login(
    payload: LoginRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    result = await auth_service.login(payload.email, payload.password)
```

---

## 📊 MODELS — Data Structures

### `app/models/identity.py`

#### `User`
```python
class User(BaseModel):
    id: str  # Unique user identifier
    email: str  # Unique email
    password_hash: str  # bcrypt hashed
    full_name: str
    email_verified: bool = False  # Email verification flag
    created_at: datetime
```

**Flow:**
- Register → User oluştur (password_hash'lenmiş)
- Email verify → email_verified = True set et
- Login → User.find_by_email() + password verification

---

#### `Organization`
```python
class Organization(BaseModel):
    id: str
    name: str  # Company name
    slug: str  # URL-safe (unique)
    owner_id: str  # User who created it
    created_at: datetime
```

**Flow:**
- Register → Organization oluştur (owner_id = user_id)
- Ownership check: org.owner_id == user_id

---

#### `Workspace`
```python
class Workspace(BaseModel):
    id: str
    organization_id: str
    name: str  # "Support", "Sales", "Marketing"
    slug: str  # URL-safe identifier
    created_at: datetime
```

**Flow:**
- Register → Default Workspace ("Support") oluştur
- Future: User workspace seçebilecek

---

#### `Member`
```python
class Member(BaseModel):
    id: str
    organization_id: str
    user_id: str
    status: MemberStatus  # ACTIVE, INACTIVE, INVITED, SUSPENDED
    team_ids: list[str] = []
    created_at: datetime
```

**Flow:**
- Register → Member oluştur (status=ACTIVE, org_id=new org)
- Login → Member.find_many(org_id) + status check
- Member status SUSPENDED → Login denied

---

#### `Role`
```python
class Role(BaseModel):
    id: str
    organization_id: str
    name: str  # "Admin", "Manager", "Agent", "Viewer"
    permissions: list[str]  # ["conversation:read", "member:write", ...]
    created_at: datetime
```

**Flow:**
- Register → seed_default_roles() 4 role oluştur
- Login → Member'ın role_ids'lerini al

---

#### `MemberRole` ⭐ (Owner Role Assignment)
```python
class MemberRole(BaseModel):
    id: str
    organization_id: str
    member_id: str
    role_id: str  # Hangi role assigned
    assigned_by: str  # User ID who did it (owner'da self)
    assigned_at: datetime
    expires_at: datetime | None  # Temporary role support
```

**Flow:**
- Register → MemberRole oluştur (member_id → admin_role_id)
- Login → member_roles = find_many(member_id) → roles list al
- Token içine roles konuyor: `access_token.roles = [admin_role_id]`

---

## 🗂️ SCHEMAS — HTTP Request/Response

### `app/schemas/auth.py`

#### Requests

**RegisterRequest**
```python
class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str
    organization_name: str  # Multi-tenant
```

**LoginRequest**
```python
class LoginRequest(BaseModel):
    email: str
    password: str
```

**RefreshTokenRequest**
```python
class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

**VerifyEmailRequest**
```python
class VerifyEmailRequest(BaseModel):
    token: str  # Email verification token
```

---

#### Responses

**TokenResponse** — `/login`, `/refresh` response
```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds
    user_id: Optional[str]  # From login/register
    member_id: Optional[str]
    organization_id: Optional[str]
```

**RegisterResponse** — `/register` response
```python
class RegisterResponse(BaseModel):
    user_id: str
    email: str
    verification_token: str  # Dev/testing only
    verification_link: str  # ${FRONTEND_URL}/verify-email?token=...
```

**CurrentUserResponse** — `/me` endpoint
```python
class CurrentUserResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    organization_id: str
    workspace_id: str
    member_id: str
    roles: list[str]  # Role IDs
    permissions: list[str]  # Derived from roles
```

**VerifyEmailResponse** — `/verify-email` response
```python
class VerifyEmailResponse(BaseModel):
    user_id: str
    email: str
    message: str
```

---

## 🔧 SERVICES — Business Logic

### `app/services/auth/authentication_service.py`

#### `register(email, password, full_name, organization_name)`

**Flow:**
```
1. Email exists? → ConflictError
2. Hash password (bcrypt)
3. Create User
4. Create Organization (slug unique)
5. Create default Workspace ("Support")
6. Seed default Roles (Admin/Manager/Agent/Viewer)
7. Create Member (status=ACTIVE)
8. Create MemberRole (Member → Admin role)  ⭐
9. Seed default Labels
10. Audit log
11. Return: {user_id, member_id, org_id, workspace_id, role_ids}
```

**Returns:**
```python
{
    "user_id": "usr_123",
    "member_id": "mem_456",
    "organization_id": "org_789",
    "organization_name": "Acme Inc.",
    "workspace_id": "ws_101",
    "role_ids": ["role-admin"]
}
```

---

#### `verify_email(verification_token)`

**Flow:**
```
1. Token'ı Redis'te arat (REDIS_PREFIX_EMAIL_VERIFICATION)
2. Token valid? → user_id decode et
3. User.update(email_verified=True)
4. Redis'ten token sil
5. Return: user_id
```

**Raises:**
- `UnauthorizedError` — Invalid/expired token

---

#### `login(email, password)`

**Flow:**
```
1. User.find_by_email(email)
2. email_verified check → Unverified users can't login
3. Password verification (bcrypt)
4. Member.find_many(organization_id)
5. Member status check → ACTIVE only
6. MemberRole.find_many(member_id) → role_ids list
7. Create tokens (access + refresh)
8. Store refresh token in Redis
9. Audit log ("user_logged_in")
10. Return: {access_token, refresh_token, expires_in, user_id, member_id, org_id, role_ids}
```

**Raises:**
- `UnauthorizedError` — Email not verified, member suspended, etc
- Generic "Invalid credentials" — For security (credential enumeration prevention)

---

#### `logout(user_id)`

**Flow:**
```
1. Revoke refresh token from Redis
2. Audit log ("user_logged_out")
3. Return: success
```

**Note:** Access token (JWT) stateless olduğu için logout'ta direkt invalid olmaz. 
Future: Token blacklist implementasyonu düşünülecek.

---

#### `refresh_access_token(refresh_token)`

**Flow:**
```
1. Decode refresh token (security.py)
2. Check type == "refresh"
3. Validate in Redis (not revoked)
4. Create new access_token (same claims)
5. Return: {access_token, refresh_token, expires_in, ...}
```

---

### `app/services/auth/token_service.py`

#### `create_tokens(user_id, org_id, member_id, roles)`

**Access Token Payload:**
```python
{
    "user_id": "usr_123",
    "org_id": "org_789",
    "member_id": "mem_456",
    "roles": ["role-admin"],
    "type": "access",
    "iat": 1234567890,
    "exp": 1234567890 + 1800  # 30 minutes
}
```

**Refresh Token Payload:**
```python
{
    "user_id": "usr_123",
    "org_id": "org_789",
    "type": "refresh",
    "iat": 1234567890,
    "exp": 1234567890 + 604800  # 7 days
}
```

**Returns:**
```python
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_in": 1800  # Seconds
}
```

**Redis Storage:**
- Key: `refresh_token:{user_id}`
- Value: `{refresh_token_string}`
- TTL: 7 days

---

#### `create_email_verification_token(user_id, email)`

**Token Payload:**
```python
{
    "user_id": "usr_123",
    "email": "user@example.com",
    "type": "email_verification",
    "iat": 1234567890,
    "exp": 1234567890 + 86400  # 24 hours
}
```

**Redis Storage:**
- Key: `email_verification:{verification_token}`
- Value: `{user_id}`
- TTL: 24 hours

---

#### `verify_email_token(token) → str (user_id)`

**Flow:**
1. Decode token (check type == "email_verification")
2. Lookup Redis key
3. If found → return user_id
4. If not found → raise UnauthorizedError

---

### `app/services/auth/password_service.py`

```python
class PasswordService:
    def hash_password(password: str) → str
        # bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    
    def verify_password(password: str, hash: str) → bool
        # bcrypt.checkpw(password.encode(), hash.encode())
```

---

### `app/services/auth/role_service.py`

#### `seed_default_roles(org_id)`

**Creates 4 roles per organization:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| Admin | All (32) | Owner/Admin — full control |
| Manager | Team/Report (10) | Team leads |
| Agent | Conversation (8) | Support agents |
| Viewer | Read-only (4) | Stakeholders |

**Returns:**
```python
{
    "admin_role_id": "role_abc",
    "manager_role_id": "role_def",
    "agent_role_id": "role_ghi",
    "viewer_role_id": "role_jkl"
}
```

---

### `app/services/auth/label_service.py`

#### `seed_default_labels(org_id)`

**Creates 6 labels per organization:**
- New (blue)
- Waiting (yellow)
- Urgent (red)
- VIP (gold)
- Spam (gray)
- Resolved (green)

---

## 🌐 ROUTERS — HTTP Endpoints

### `app/routers/auth.py`

#### `POST /auth/register`

**Request:**
```json
{
  "email": "owner@acme.com",
  "password": "securepass123",
  "full_name": "John Doe",
  "organization_name": "Acme Inc."
}
```

**Response:** `RegisterResponse`
```json
{
  "user_id": "usr_123",
  "email": "owner@acme.com",
  "verification_token": "eyJ0eXAi...",  // Dev only
  "verification_link": "http://localhost:3000/verify-email?token=eyJ0eXAi..."
}
```

**Flow:**
```
Dependency: auth_service
→ auth_service.register() — Creates everything
→ token_service.create_email_verification_token() — Email verification
→ Return RegisterResponse
```

**Errors:**
- `409 CONFLICT` — Email already exists
- `400 BAD REQUEST` — General registration failure

---

#### `POST /auth/verify-email`

**Request:**
```json
{
  "token": "eyJ0eXAi..."
}
```

**Response:** `VerifyEmailResponse`
```json
{
  "user_id": "usr_123",
  "email": "owner@acme.com",
  "message": "Email verified successfully"
}
```

**Flow:**
```
Dependency: auth_service
→ auth_service.verify_email(token) — Updates user.email_verified=true
→ Return VerifyEmailResponse
```

---

#### `POST /auth/login`

**Request:**
```json
{
  "email": "owner@acme.com",
  "password": "securepass123"
}
```

**Response:** `TokenResponse`
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "usr_123",
  "member_id": "mem_456",
  "organization_id": "org_789"
}
```

**Flow:**
```
Dependency: auth_service
→ auth_service.login(email, password)
  ├─ User.find_by_email()
  ├─ email_verified check
  ├─ Password verification
  ├─ Member.find_many()
  ├─ MemberRole.find_many() → role_ids
  └─ token_service.create_tokens()
→ Return TokenResponse
```

**Errors:**
- `401 UNAUTHORIZED` — Invalid credentials (generic)

---

#### `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJ0eXAi..."
}
```

**Response:** `TokenResponse` (new access_token)

**Flow:**
```
Dependency: auth_service
→ auth_service.refresh_access_token(refresh_token)
  ├─ Decode + validate refresh token
  ├─ Check Redis (not revoked)
  └─ token_service.create_access_token_from_refresh()
→ Return TokenResponse
```

---

#### `POST /auth/logout`

**Request:** (Authenticated, no body)

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

**Headers:**
```
Authorization: Bearer eyJ0eXAi...
```

**Flow:**
```
Dependency: current_user (get_current_user)
Dependency: auth_service
→ Extract user_id from token
→ auth_service.logout(user_id)
  └─ token_service.revoke_refresh_token()
→ Return success
```

---

#### `GET /me` — Current User Profile

**Request:** (Authenticated)

**Response:** `CurrentUserResponse`
```json
{
  "user_id": "usr_123",
  "email": "owner@acme.com",
  "full_name": "John Doe",
  "organization_id": "org_789",
  "workspace_id": "ws_101",
  "member_id": "mem_456",
  "roles": ["role-admin"],
  "permissions": [
    "conversation:read",
    "conversation:write",
    "member:read",
    "member:write",
    ...
  ]
}
```

**Flow:**
```
Dependency: current_user (get_current_user)
→ Extract from JWT payload
→ Fetch user details from DB (if email_verified missing)
→ Compute permissions from roles
→ Return CurrentUserResponse
```

---

## 💾 REPOSITORIES — Database Access

### `app/repositories/base.py`

**Generic CRUD operations with ObjectId handling:**

```python
async def create(model: T) → str
    # Insert → return document ID

async def read(document_id: str) → T | None
    # Find by ID (handles ObjectId ↔ string conversion)

async def update(document_id: str, update_dict: dict) → bool
    # Update fields

async def find(filter_dict: dict) → T | None
    # Find single by filter

async def find_many(filter_dict: dict, skip, limit) → list[T]
    # Find multiple (converts MongoDB's ObjectId to string)

async def delete(document_id: str) → bool
    # Delete
```

**Key Fix (ObjectId Conversion):**
```python
# MongoDB returns ObjectId, Pydantic models expect string
if "_id" in doc and isinstance(doc["_id"], ObjectId):
    doc["_id"] = str(doc["_id"])  # ✅ Convert before validation
```

---

### `app/repositories/identity.py`

#### `UserRepository`
```python
async def find_by_email(email: str) → User | None
    # Find user by email (unique)

async def find_by_id(user_id: str) → User | None
    # Standard read()

async def find_many_by_org(org_id: str) → list[User]
    # All users in organization
```

**Collections:**
- Database collection: `users`
- Fields: `id`, `email`, `password_hash`, `full_name`, `email_verified`, `created_at`

---

#### `OrganizationRepository`
```python
async def find_by_slug(slug: str) → Organization | None
    # Find by organization slug (unique)

async def find_by_owner(owner_id: str) → list[Organization]
    # Organizations owned by user
```

---

#### `WorkspaceRepository`
```python
async def find_by_org(org_id: str) → list[Workspace]
    # All workspaces in organization

async def find_default(org_id: str) → Workspace | None
    # Default workspace per org
```

---

#### `MemberRepository`
```python
async def find_by_user_and_org(user_id: str, org_id: str) → Member | None

async def find_many(filter_dict: dict) → list[Member]
    # Members with filter (e.g., org_id, status)

async def find_by_org(org_id: str) → list[Member]
```

---

#### `RoleRepository`
```python
async def find_by_org(org_id: str) → list[Role]

async def find_by_name(org_id: str, name: str) → Role | None
    # Admin, Manager, Agent, Viewer
```

---

#### `MemberRoleRepository` ⭐
```python
async def find_by_member(member_id: str) → list[MemberRole]
    # All role assignments for a member

async def find_many(filter_dict: dict) → list[MemberRole]
    # Filter by member_id, role_id, org_id
```

---

## 🔄 Complete Auth Flow — End-to-End

### Register Flow

```
User → Frontend (POST /auth/register)
         ↓
    Router (app/routers/auth.py:register)
         ↓
    AuthenticationService.register()
         ├─ UserRepository.find_by_email() ✓
         ├─ PasswordService.hash_password() ✓
         ├─ UserRepository.create(User) ✓
         ├─ OrganizationRepository.create(Organization) ✓
         ├─ WorkspaceRepository.create(Workspace) ✓
         ├─ RoleService.seed_default_roles() ✓
         │   └─ RoleRepository.create() x4 (Admin/Manager/Agent/Viewer)
         ├─ MemberRepository.create(Member) ✓
         ├─ MemberRoleRepository.create(MemberRole) ✓ — Owner → Admin
         ├─ LabelService.seed_default_labels() ✓
         └─ BaseService.log_action() ✓
         ↓
    TokenService.create_email_verification_token()
         ├─ JWT encode (user_id, email, type=email_verification)
         └─ Redis.setex() — store for 24h
         ↓
    Response: RegisterResponse
         └─ verification_link: "http://frontend/verify?token=..."
```

### Email Verification Flow

```
User → Email link (GET /verify-email?token=...)
         ↓
    Router (POST /auth/verify-email)
         ↓
    AuthenticationService.verify_email()
         ├─ TokenService.verify_email_token()
         │   ├─ JWT decode
         │   └─ Redis.get() — retrieve user_id
         ├─ UserRepository.update(email_verified=true)
         └─ Redis.delete() — invalidate token
         ↓
    Response: VerifyEmailResponse
         └─ "Email verified successfully"
```

### Login Flow

```
User → Frontend (POST /auth/login)
         ↓
    Router (app/routers/auth.py:login)
         ↓
    AuthenticationService.login()
         ├─ UserRepository.find_by_email() ✓
         ├─ Check email_verified ✓
         ├─ PasswordService.verify_password() ✓
         ├─ MemberRepository.find_many(org_id) ✓
         ├─ Check Member.status == ACTIVE ✓
         ├─ MemberRoleRepository.find_many(member_id) ✓ — Get role_ids
         └─ TokenService.create_tokens()
            ├─ JWT encode (access_token with roles)
            ├─ JWT encode (refresh_token)
            └─ Redis.setex(refresh_token) — store for 7d
         ↓
    Response: TokenResponse
         ├─ access_token (30 min)
         ├─ refresh_token (7 days)
         ├─ user_id, member_id, org_id
         └─ roles = ["role-admin"]
```

### Token Refresh Flow

```
Client → Frontend (POST /auth/refresh)
            ↓
    Router (app/routers/auth.py:refresh_token)
         ↓
    AuthenticationService.refresh_access_token()
         ├─ TokenService.verify_refresh_token()
         │   ├─ JWT decode
         │   ├─ Check type == "refresh"
         │   └─ Redis.get() — check not revoked
         └─ TokenService.create_access_token_from_refresh()
            └─ JWT encode (new access_token, same claims)
         ↓
    Response: TokenResponse (new access_token)
```

### Logout Flow

```
User → Frontend (POST /auth/logout)
          ↓
    Router (app/routers/auth.py:logout)
         ↓
    Dependency: get_current_user(request)
         ├─ Extract Bearer token
         └─ decode_token() + validate
         ↓
    AuthenticationService.logout()
         ├─ TokenService.revoke_refresh_token()
         │   └─ Redis.delete(refresh_token_key)
         └─ BaseService.log_action("user_logged_out")
         ↓
    Response: {"message": "Logged out successfully"}
```

---

## 🔗 Data Relationships

```
User
  ├─ id (PK)
  ├─ email (UNIQUE)
  └─ email_verified ←─ Email verification
        ↓
    Organization (created during register)
        ├─ id (PK)
        ├─ owner_id (FK → User.id)
        ├─ slug (UNIQUE)
        └─ created_at
              ↓
        ├─ Workspace
        │   ├─ id (PK)
        │   ├─ organization_id (FK)
        │   └─ name ("Support")
        │
        ├─ Member
        │   ├─ id (PK)
        │   ├─ user_id (FK → User.id)
        │   ├─ organization_id (FK)
        │   ├─ status (ACTIVE)
        │   └─ created_at
        │        ↓
        │        └─ MemberRole ⭐ (Owner → Admin)
        │            ├─ id (PK)
        │            ├─ member_id (FK)
        │            ├─ role_id (FK → Role.id)
        │            └─ assigned_by (FK → User.id)
        │
        ├─ Role (4 seeded)
        │   ├─ id (PK)
        │   ├─ name ("Admin"/"Manager"/"Agent"/"Viewer")
        │   ├─ organization_id (FK)
        │   └─ permissions (array)
        │
        └─ Label (6 seeded)
            ├─ id (PK)
            ├─ name ("New"/"Waiting"/...)
            ├─ organization_id (FK)
            └─ color
```

---

## 📋 Authentication Checklist

- ✅ User registration with email verification
- ✅ Organization auto-creation (multi-tenant)
- ✅ Owner role assignment via MemberRole
- ✅ JWT access + refresh tokens
- ✅ Token expiry & refresh
- ✅ Member status validation
- ✅ Role-based permissions
- ✅ Audit logging
- ⏳ Token blacklist (logout stateless JWT)
- ⏳ Rate limiting on login/register
- ⏳ Workspace selection in login
- ⏳ Email sending (currently mocked)

---

## 📌 Key Files by Purpose

| Purpose | Files |
|---------|-------|
| **Configuration** | `core/config.py` |
| **JWT Operations** | `core/security.py`, `services/auth/token_service.py` |
| **User Management** | `models/identity.py::User`, `repositories/identity.py::UserRepository` |
| **Organization** | `models/identity.py::Organization`, `repositories/identity.py::OrganizationRepository` |
| **Member & Roles** | `models/identity.py::Member/MemberRole`, `repositories/identity.py::MemberRepository/MemberRoleRepository` |
| **Business Logic** | `services/auth/authentication_service.py` |
| **HTTP Endpoints** | `routers/auth.py` |
| **Request/Response** | `schemas/auth.py` |
| **Dependency Injection** | `dependencies.py` |

---

**Last Updated:** 2026-08-03  
**Maintained by:** SparkQuark Engineering Team
