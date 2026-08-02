# Business Logic & Service Architecture

**Status**: Complete | **Last Updated**: Aug 2, 2026  
**Scope**: Service layer design, domain logic, data flows, multi-tenant patterns

---

## Overview

BoltChats is built on a **multi-tenant, service-driven architecture** where business logic lives exclusively in the service layer. This document explains:

1. **Architecture Philosophy** — Why we structure services this way
2. **Domain-Driven Design** — How we organize code around domains
3. **Service Layer Patterns** — Base classes, error handling, logging
4. **Multi-Tenant Implementation** — How tenant isolation works
5. **Key Business Flows** — End-to-end examples (auth, conversations, etc.)
6. **Data Access Patterns** — Repository + service choreography

---

## 1. Architecture Philosophy

### Core Principles

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Router Layer                   │
│         (HTTP endpoints, request validation)        │
└─────────────────┬───────────────────────────────────┘
                  │ Depends() injection
                  ▼
┌─────────────────────────────────────────────────────┐
│           Service Layer (Business Logic)            │
│  - All validation, authorization, state changes    │
│  - Service → Service orchestration                  │
│  - Domain events published here                     │
│  - Audit logging / compliance                       │
└─────────────────┬───────────────────────────────────┘
                  │ Uses
                  ▼
┌─────────────────────────────────────────────────────┐
│      Repository Layer (Data Access Only)           │
│  - CRUD operations only                            │
│  - Query optimization (filtering, pagination)      │
│  - No business logic, no authorization             │
└─────────────────────────────────────────────────────┘
```

### Why This Layering?

**Router**: Thin translation layer between HTTP and Python
- Parses request → Calls ONE service method → Translates response
- No loops, no conditionals, no business logic
- Example: `register(payload) → auth_service.register() → return TokenResponse`

**Service**: All domain logic lives here
- Validation: "Is email valid?" "Does user already exist?"
- Authorization: "Can this user access this org?"
- State changes: Create/update/delete domain objects
- Audit: Log what happened for compliance
- Events: Publish domain events (user_registered, conversation_started)

**Repository**: Simple data persistence
- `find()`, `find_many()`, `create()`, `update()`, `delete()`
- Index-aware queries: `find_by_slug()`, `find_by_email()`
- No filtering logic, no authorization checks

### Router ← Service Dependency Injection

```python
# services/auth/authentication_service.py
class AuthenticationService(BaseService):
    async def register(self, email: str, password: str, 
                      full_name: str, organization_name: str) -> dict:
        """Register new user with new org (multi-tenant)"""
        # 1. Validate (service's job)
        existing_user = await self.users.find_by_email(email)
        if existing_user:
            raise ConflictError(f"Email {email} already registered")
        
        # 2. Check org slug uniqueness
        slug = generate_slug(organization_name)
        existing_org = await self.organizations.find_by_slug(slug)
        if existing_org:
            raise ConflictError(f"Org slug taken")
        
        # 3. Create domain objects (service choreography)
        hashed_password = self.password_service.hash_password(password)
        user = User(email=email, password_hash=hashed_password, full_name=full_name)
        user_id = await self.users.create(user)
        
        organization = Organization(name=organization_name, slug=slug, owner_id=user_id)
        org_id = await self.organizations.create(organization)
        
        member = Member(organization_id=org_id, user_id=user_id, status=MemberStatus.ACTIVE)
        member_id = await self.members.create(member)
        
        # 4. Audit log
        await self.log_action("user_registered", resource_id=user_id, ...)
        
        return {"user_id": user_id, "member_id": member_id, "organization_id": org_id}

# routers/auth.py
@router.post("/register")
async def register(
    payload: RegisterRequest,
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    """Register user"""
    try:
        result = await auth_service.register(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            organization_name=payload.organization_name,
        )
        tokens = await token_service.create_tokens(...)
        return TokenResponse(...)
    except ConflictError as e:
        raise HTTPException(409, detail=str(e))
```

**Key**: Router just orchestrates the call; `AuthenticationService.register()` does all the work.

---

## 2. Domain-Driven Design Organization

Services are organized by **domain**, not technical layer:

```
services/
├── auth/                    # Domain: User identity
│   ├── authentication_service.py   # register, login, logout
│   ├── token_service.py            # JWT creation/validation
│   ├── password_service.py          # bcrypt hashing
│   └── __init__.py
│
├── organization/            # Domain: Org structure
│   ├── organization_service.py      # org CRUD
│   ├── workspace_service.py         # workspace CRUD
│   ├── member_service.py            # member management
│   ├── team_service.py              # team management
│   ├── role_service.py              # role definitions
│   ├── invitation_service.py        # email invitations
│   └── __init__.py
│
├── conversation/            # Domain: Customer communication
│   ├── conversation_service.py      # create, list, search
│   ├── message_service.py           # message CRUD + threading
│   ├── customer_service.py          # customer profiles
│   ├── draft_service.py             # draft messages
│   ├── label_service.py             # message labels/tags
│   └── __init__.py
│
├── security/                # Domain: Access control
│   ├── permission_service.py        # RBAC checks
│   └── __init__.py
│
├── integration/             # Domain: Provider connections
│   ├── integration_service.py       # provider auth
│   ├── provider_factory.py          # provider strategy pattern
│   └── __init__.py
│
├── notification/            # Domain: Multi-channel notify
│   ├── notification_service.py      # email, SMS, push
│   ├── notification_provider_factory.py
│   └── __init__.py
│
├── events/                  # Domain: Event streaming
│   ├── event_bus.py                 # publish/subscribe
│   ├── event_consumer.py            # event handlers
│   ├── workflow_service.py          # automation
│   └── __init__.py
│
└── base.py                  # Base class for all services
```

**Benefits**:
- Service organized by **business capability**, not technical concerns
- Easy to find where logic lives: "Where's conversation creation?" → `conversation/conversation_service.py`
- Supports independent team ownership (Team A owns `auth/`, Team B owns `organization/`)
- Services can be replaced, tested, versioned independently

---

## 3. Service Layer Patterns

### BaseService — Common Patterns for All Services

```python
# services/base.py
from motor.motor_asyncio import AsyncIOMotorDatabase
import structlog

class BaseService:
    """Base service with common patterns"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def log_action(
        self,
        action: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Audit trail for compliance"""
        await structlog.get_logger().info(
            "audit_log",
            action=action,
            resource_id=resource_id,
            resource_type=resource_type,
            details=details,
        )
```

**Every service**:
- Inherits `BaseService`
- Gets `self.db` (Motor async MongoDB client)
- Can call `await self.log_action()` for audit logs
- Throws domain exceptions: `ConflictError`, `UnauthorizedError`, `ForbiddenError`

### Custom Exceptions — Semantic Error Handling

```python
# services/base.py
class AppError(Exception):
    """Base app error"""
    pass

class ConflictError(AppError):
    """Resource already exists (409)"""
    pass

class UnauthorizedError(AppError):
    """Authentication failed (401)"""
    pass

class ForbiddenError(AppError):
    """Authorization failed (403)"""
    pass

class NotFoundError(AppError):
    """Resource not found (404)"""
    pass

class ValidationError(AppError):
    """Invalid input (400)"""
    pass
```

**Usage in service**:
```python
async def login(self, email: str, password: str) -> dict:
    user = await self.users.find_by_email(email)
    if not user:
        raise UnauthorizedError("Invalid email or password")  # 401, audit logged
    
    if not self.password_service.verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    
    # ... create tokens
    return tokens
```

**Router catches and translates**:
```python
@router.post("/login")
async def login(payload: LoginRequest, auth_service = Depends(...)):
    try:
        result = await auth_service.login(payload.email, payload.password)
        return TokenResponse(...)
    except ConflictError as e:
        raise HTTPException(409, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(401, detail="Invalid credentials")
    except Exception as e:
        await logger.aerror("login_failed", error=str(e))  # Log for debugging
        raise HTTPException(400, detail="Login failed")
```

### Dependency Injection Pattern

```python
# dependencies.py
async def get_authentication_service() -> AsyncGenerator[AuthenticationService, None]:
    """Dependency factory — creates service with all dependencies"""
    from app.services.auth import AuthenticationService, TokenService
    from app.core.config import settings
    
    db = get_database()
    redis = get_redis()
    token_service = TokenService(redis, settings)
    service = AuthenticationService(db, redis, token_service)
    yield service
```

**Why this pattern?**
- Each endpoint gets a fresh service instance
- All repositories, clients (Redis, MongoDB) injected
- Easy to mock in tests: `@patch('get_authentication_service')`
- Circular imports prevented by lazy imports (imports inside function)

---

## 4. Multi-Tenant Implementation

### Tenant Isolation Strategy

**Key Insight**: Multi-tenant means **one database, many organizations**.

```
MongoDB
├── users collection
│   ├── user_1 (email: john@acme.com)
│   └── user_2 (email: jane@techcorp.com)
│
├── organizations collection
│   ├── org_1 (name: "Acme Corp", owner_id: user_1, slug: "acme-corp")
│   └── org_2 (name: "TechCorp", owner_id: user_2, slug: "techcorp")
│
├── members collection
│   ├── member_1 (user_id: user_1, org_id: org_1, status: ACTIVE)  ← john in Acme
│   ├── member_2 (user_id: user_1, org_id: org_2, status: ACTIVE)  ← john also in TechCorp
│   └── member_3 (user_id: user_2, org_id: org_2, status: ACTIVE)  ← jane in TechCorp
│
└── conversations collection
    ├── conv_1 (org_id: org_1, ...)  ← belongs to Acme only
    └── conv_2 (org_id: org_2, ...)  ← belongs to TechCorp only
```

### Register Flow — Multi-Tenant

```python
async def register(self, email: str, password: str, full_name: str,
                  organization_name: str) -> dict:
    """Each new user gets their own organization"""
    
    # 1. Verify email unique (global constraint)
    existing = await self.users.find_by_email(email)
    if existing:
        raise ConflictError("Email already registered")
    
    # 2. Create user
    hashed = self.password_service.hash_password(password)
    user = User(email=email, password_hash=hashed, full_name=full_name)
    user_id = await self.users.create(user)
    
    # 3. Generate org slug (auto-generated from name)
    slug = generate_slug(organization_name)
    existing_org = await self.organizations.find_by_slug(slug)
    if existing_org:
        raise ConflictError("Organization name taken")
    
    # 4. Create organization (new user is owner)
    org = Organization(
        name=organization_name,
        slug=slug,
        owner_id=user_id,  # ← Key: user owns their org
    )
    org_id = await self.organizations.create(org)
    
    # 5. Create member record (user in their org)
    member = Member(
        organization_id=org_id,
        user_id=user_id,
        status=MemberStatus.ACTIVE,
    )
    member_id = await self.members.create(member)
    
    # 6. Audit & return
    await self.log_action("user_registered", resource_id=user_id,
                         details={"org_id": org_id, "org_name": organization_name})
    
    return {
        "user_id": user_id,
        "member_id": member_id,
        "organization_id": org_id,
    }
```

### Login Flow — Tenant Selection

```python
async def login(self, email: str, password: str) -> dict:
    """User can be in multiple orgs; pick first active membership"""
    
    # 1. Find user globally
    user = await self.users.find_by_email(email)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    
    # 2. Verify password
    if not self.password_service.verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    
    # 3. Find all memberships for this user
    members = await self.members.find_many({"user_id": user.id})
    if not members:
        raise UnauthorizedError("User has no organization membership")
    
    # 4. Filter for ACTIVE status (can be SUSPENDED, ARCHIVED, etc.)
    active_members = [m for m in members if m.status == MemberStatus.ACTIVE]
    if not active_members:
        raise UnauthorizedError("No active organization membership")
    
    # 5. Pick first active (future: let user choose org)
    member = active_members[0]
    org_id = member.organization_id
    
    # 6. Fetch member's roles from this org
    member_roles = await MemberRoleRepository(self.db).find_many(
        {"member_id": member.id}
    )
    role_ids = [mr.role_id for mr in (member_roles or [])]
    
    # 7. Create tokens with org_id + member_id
    tokens = await self.token_service.create_tokens(
        user_id=user.id,
        org_id=org_id,
        member_id=member.id,
        email=user.email,
        full_name=user.full_name,
        roles=role_ids,
    )
    
    await self.log_action("user_login", resource_id=user.id,
                         details={"org_id": org_id})
    
    return {**tokens, "user_id": user.id, "member_id": member.id, "org_id": org_id}
```

### Token Payload — Multi-Tenant Awareness

```python
# When creating access token
access_payload = {
    "user_id": user_id,        # Identifies user globally
    "org_id": org_id,          # Identifies tenant
    "member_id": member_id,    # Identifies user in this org
    "roles": roles,            # Roles within this org
    "type": "access",          # Distinguish from refresh token
    "iat": datetime.now(timezone.utc),
    "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
}

access_token = jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
```

**Used by**: Every protected endpoint to know:
- Which user made the request
- Which organization's data to access
- What permissions the user has

---

## 5. Key Business Flows

### Flow 1: User Registration → Organization Creation

```
POST /api/v1/auth/register
{
  "email": "john@acme.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "organization_name": "Acme Corporation"
}

1. Router validates RegisterRequest schema
   ├─ email: valid email format
   ├─ password: >= 8 chars
   ├─ full_name: non-empty
   └─ organization_name: non-empty

2. Calls auth_service.register(...)
   ├─ Check email not already registered (global)
   ├─ Hash password with bcrypt
   ├─ Create User doc in MongoDB
   ├─ Generate slug from org name ("acme-corporation")
   ├─ Check slug not taken (org name unique)
   ├─ Create Organization doc (owner_id = user_id)
   ├─ Create Member doc (user in new org, ACTIVE status)
   ├─ Log audit event: user_registered
   └─ Return {user_id, member_id, organization_id}

3. Calls token_service.create_tokens(user_id, org_id, member_id, ...)
   ├─ Generate access token (30 min expiry)
   │   payload: {user_id, org_id, member_id, roles, type: "access"}
   ├─ Generate refresh token (7 day expiry)
   │   payload: {user_id, org_id, type: "refresh"}
   ├─ Store refresh token hash in Redis
   └─ Return {access_token, refresh_token, expires_in: 1800}

4. Router returns TokenResponse
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "6a6f880f27f45641c52530b3",
  "member_id": "6a6f880f27f45641c52530b5",
  "organization_id": "6a6f880f27f45641c52530b4"
}

Client stores tokens, uses access_token in Authorization header.
```

### Flow 2: User Login → Token Issue

```
POST /api/v1/auth/login
{
  "email": "john@acme.com",
  "password": "SecurePass123!"
}

1. Router validates LoginRequest

2. Calls auth_service.login(email, password)
   ├─ Find user by email (global query)
   ├─ Verify password (bcrypt)
   ├─ Find all Member records for this user
   ├─ Filter for ACTIVE status (skip SUSPENDED/ARCHIVED)
   ├─ Pick first active membership (user_id + org_id)
   ├─ Fetch user's roles in this org
   ├─ Log audit event: user_login
   └─ Return {access_token, refresh_token, user_id, member_id, org_id}

3. Router returns TokenResponse (same format as register)

Key difference from register:
- register creates new org; login picks existing org
- login checks member status (ACTIVE only)
```

### Flow 3: Protected Endpoint Access

```
GET /api/v1/conversations
Authorization: Bearer eyJ...  ← access token

1. Router dependency: @Depends(get_current_user)
   ├─ Extract token from header
   ├─ Decode with JWT (verify signature)
   ├─ Check type == "access" (not refresh)
   ├─ Extract: user_id, org_id, member_id, roles
   ├─ Verify token not revoked in Redis
   └─ Return {user_id, org_id, member_id, roles, ...}

2. Router calls conversation_service.list_conversations(
       current_user["org_id"],     ← limit to this org only
       current_user["member_id"],
       current_user["roles"]
   )

3. Service layer validates authorization
   ├─ Check member is ACTIVE in org
   ├─ Check member has permission to view conversations
   └─ Only return conversations where org_id == request org_id

4. Return conversations filtered to tenant
```

### Flow 4: Token Refresh

```
POST /api/v1/auth/refresh
{
  "refresh_token": "eyJ..."
}

1. Calls auth_service.refresh_access_token(refresh_token)
   ├─ Verify refresh token signature
   ├─ Check type == "refresh" (not access)
   ├─ Check token not revoked in Redis
   ├─ Extract user_id, org_id from payload
   ├─ Re-fetch member from DB (check status still ACTIVE)
   ├─ If member ARCHIVED/SUSPENDED, raise error
   ├─ Re-fetch member's current roles from DB
   ├─ Create NEW access token with fresh data
   └─ Return {new access_token, expires_in: 1800}

Key insight:
- Refresh token stays same (reuse)
- Access token replaced (fresh roles, status)
- Member status checked on every refresh
- → If admin suspends user, next refresh fails
```

---

## 6. Data Access Patterns

### Repository Pattern — Data Access Only

```python
# repositories/identity.py
class UserRepository(BaseRepository[User]):
    async def find_by_email(self, email: str) -> User | None:
        """Find user by email (global query)"""
        return await self.find({"email": email})
    
    async def find_by_id(self, user_id: str) -> User | None:
        return await self.read(user_id)

class OrganizationRepository(BaseRepository[Organization]):
    async def find_by_slug(self, slug: str) -> Organization | None:
        """Find org by slug (ensure uniqueness)"""
        return await self.find({"slug": slug})
    
    async def find_by_owner(self, owner_id: str) -> list[Organization]:
        """Find all orgs owned by user"""
        return await self.find_many({"owner_id": owner_id})

class MemberRepository(BaseRepository[Member]):
    async def find_by_org(self, org_id: str, active_only: bool = True) -> list[Member]:
        """Find all members in org (optionally filter ACTIVE)"""
        filter_dict = {"organization_id": org_id}
        if active_only:
            filter_dict["status"] = "active"
        return await self.find_many(filter_dict)
```

**Key principle**: No logic in repository
- `find_by_email()` → Find user, return User or None
- `find_by_slug()` → Find org, return Organization or None
- Repositories don't check permissions, validate, or decide what to do with the data

### Service Uses Repository

```python
class AuthenticationService(BaseService):
    def __init__(self, db: AsyncIOMotorDatabase, ...):
        self.users = UserRepository(db)
        self.members = MemberRepository(db)
        self.organizations = OrganizationRepository(db)
    
    async def login(self, email: str, password: str) -> dict:
        # 1. Repository finds data
        user = await self.users.find_by_email(email)
        
        # 2. Service validates business logic
        if not user:
            raise UnauthorizedError("Invalid credentials")
        
        if not self.password_service.verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")
        
        # 3. Repository finds member data
        members = await self.members.find_many({"user_id": user.id})
        
        # 4. Service filters by business rule (ACTIVE only)
        active_members = [m for m in members if m.status == MemberStatus.ACTIVE]
        if not active_members:
            raise UnauthorizedError("No active membership")
        
        # 5. Service creates tokens, returns result
        member = active_members[0]
        tokens = await self.token_service.create_tokens(...)
        return {**tokens, "member_id": member.id, "org_id": member.organization_id}
```

---

## 7. Error Handling & Observability

### Error Handling Hierarchy

```python
# Service raises domain exception
if not user:
    raise UnauthorizedError("Invalid credentials")

# Router catches, translates to HTTP
except UnauthorizedError as e:
    await logger.aerror("login_failed", email=payload.email)
    raise HTTPException(401, detail="Invalid credentials")

# Logs captured by structlog, stored in:
# - Console (dev)
# - ELK / Datadog (prod)
```

### Audit Logging

```python
# Every state change logged
await self.log_action(
    "user_registered",
    resource_id=user_id,
    resource_type="user",
    details={
        "email": email,
        "organization_name": organization_name,
        "org_id": org_id,
    }
)

# Result in audit trail:
# {
#   "action": "user_registered",
#   "resource_id": "6a6f...",
#   "resource_type": "user",
#   "details": {...},
#   "timestamp": "2026-08-02T21:00:00Z",
#   "actor_id": "system"  (or JWT user_id if set)
# }
```

---

## Summary: The Mental Model

```
Request Flow:
  HTTP Request
      ↓
  Router validates request
      ↓
  Service performs business logic
      ├─ Validates (ConflictError, ValidationError, etc.)
      ├─ Authorizes (ForbiddenError)
      ├─ Uses Repository to access data
      ├─ Creates/updates domain objects
      ├─ Publishes events (optional)
      └─ Logs audit trail
      ↓
  Router catches exceptions
      ├─ Domain exceptions → HTTP status codes
      ├─ Logs unexpected errors
      └─ Returns response
      ↓
  HTTP Response

Multi-Tenant:
  - Token carries org_id + member_id
  - Every query filtered by org_id
  - Member status checked on auth
  - Audit log includes org context
  - All databases queries indexed by org_id

Testing:
  - Mock repositories in unit tests
  - Use real MongoDB/Redis in integration tests
  - Service logic tested independently
  - Router tested end-to-end
```

---

## Next: Implementation Examples

For concrete examples of each domain's services, see:
- `docs/AUTH_ARCHITECTURE.md` — Deep dive into auth service
- `docs/AUTH_FILES_INVENTORY.md` — Annotated auth source code
- `docs/MEMBER_ID_FLOW.md` — How member_id flows through system

For individual service patterns:
- `services/boltchats-api/app/services/<domain>/` — Source code
- `tests/unit/` — Service unit tests (mocked repos)
- `tests/integration/` — End-to-end tests (real DB)
