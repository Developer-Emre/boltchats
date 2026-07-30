# SparkQuark Step 2 - Repository Layer

**Status:** ✅ Complete  
**Date:** 2026-07-30  
**Phase:** Data Access - Repository Pattern

---

## Overview

Created complete repository layer with Motor (async MongoDB) for all SparkQuark domains.

**Pattern:** Generic base repository + domain-specific repositories
**Goal:** Clean separation between database and business logic

---

## Architecture

### Layer Stack
```
API Router (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access) ← We are here
    ↓
Motor Client (Async MongoDB)
    ↓
MongoDB Database
```

### Files Created

```
services/boltchats-api/app/repositories/
├── base.py (194 lines)               - Generic CRUD base class
├── query_builder.py (295 lines)      - Query builders, pagination
├── identity.py (206 lines)           - Identity domain repositories
├── conversation.py (293 lines)       - Conversation domain repositories
├── integration.py (295 lines)        - Integration domain repositories
└── __init__.py (54 lines)            - Exports
```

**Total:** 1,337 lines of repository code ✅

---

## 1. Base Repository Pattern

**File:** `base.py`

Generic `BaseRepository[T]` for all models:

```python
class BaseRepository(Generic[T]):
    async def create(document: T) -> str
    async def read(id: str) -> T | None
    async def update(id: str, data: dict) -> bool
    async def delete(id: str) -> bool
    async def find(filter: dict) -> T | None
    async def find_many(filter: dict, skip: int, limit: int) -> list[T]
    async def count(filter: dict) -> int
    async def exists(filter: dict) -> bool
    async def delete_many(filter: dict) -> int
    async def update_many(filter: dict, data: dict) -> int
    async def create_index(keys, unique: bool) -> str
```

**Features:**
- ✅ Generic type safety with `Generic[T]`
- ✅ Soft/hard delete detection
- ✅ Pydantic model serialization
- ✅ MongoDB ObjectId handling
- ✅ Index management
- ✅ Pagination support

---

## 2. Query Builder Utilities

**File:** `query_builder.py`

### QueryBuilder - Fluent API

```python
query = (QueryBuilder()
    .filter_by(organization_id="123", status="open")
    .filter_in("channel", ["instagram", "facebook"])
    .sort_desc("last_message_at")
    .paginate(page=2, page_size=20)
    .build())
```

**Operators:**
- `filter_by(**kwargs)` - AND conditions
- `filter_in(field, values)` - $in operator
- `filter_eq/ne/gt/gte/lt/lte(field, value)` - Comparisons
- `filter_exists(field, bool)` - Existence check
- `filter_regex(field, pattern)` - Regex search
- `filter_date_range(field, start, end)` - Date range
- `sort_asc/desc(field)` - Sorting
- `paginate(page, size)` - Pagination
- `limit(count)` / `skip(count)` - Manual limits

### PaginationParams & PaginatedResponse

```python
params = PaginationParams(page=1, page_size=20)
response = PaginatedResponse(
    data=conversations,
    total=500,
    page=1,
    page_size=20
)
# Returns: { data: [...], pagination: { page, pages, total, page_size } }
```

---

## 3. Identity Domain Repositories

**File:** `identity.py`

### OrganizationRepository
```
find_by_slug(slug)
find_by_owner(owner_id)
get_active(id)  # Only non-deleted
```

### WorkspaceRepository
```
find_by_org(org_id)
find_by_name(org_id, name)
```

### MemberRepository
```
find_by_user(org_id, user_id)
find_by_org(org_id, active_only=True)
find_by_team(team_id)
```

### MemberRoleRepository
```
find_by_member(member_id)
find_by_org(org_id)
has_role(member_id, role_id)  # Check permission
```

### TeamRepository
```
find_by_org(org_id)
find_by_name(org_id, name)
```

### RoleRepository
```
find_by_name(org_id, name)
find_by_org(org_id)
```

### InvitationRepository
```
find_by_token(token)
find_by_email(org_id, email)
find_pending(org_id)  # Non-expired, not accepted
```

---

## 4. Conversation Domain Repositories

**File:** `conversation.py`

### CustomerRepository
```
find_by_org(org_id)
find_by_email(org_id, email)
search(org_id, query)  # Name or email
```

### CustomerIdentityRepository
```
find_by_customer(customer_id)
find_by_channel(org_id, channel, external_id)
find_or_get_customer(org_id, channel, external_id)  # Resolve to customer_id
```

**Use Case:** Instagram @username → customer_id

### ConversationRepository
```
find_by_customer(org_id, customer_id)
find_by_channel(org_id, channel, external_id)  # By provider ID
find_inbox(org_id, status="open")  # Dashboard inbox
find_by_assignee(org_id, member_id)
find_by_label(org_id, label_id)
```

### ConversationParticipantRepository
```
find_by_conversation(conversation_id)
is_participant(conversation_id, member_id)
get_unread_count(conversation_id, member_id)  # For badge
```

### MessageRepository
```
find_by_conversation(conversation_id, skip, limit)  # Paginated
find_by_thread(conversation_id, parent_id)  # Message threads
find_by_external_id(org_id, external_id)  # Webhook deduplication
```

### InternalNoteRepository
```
find_by_conversation(conversation_id)
```

### LabelRepository
```
find_by_org(org_id)
find_by_name(org_id, name)
```

### ConversationDraftRepository
```
find_by_member(conversation_id, member_id)  # Get member's draft
find_by_conversation(conversation_id)
```

---

## 5. Integration Domain Repositories

**File:** `integration.py`

### IntegrationRepository
```
find_by_org(org_id)
find_by_provider(org_id, provider)
find_connected(org_id)  # Only connected
find_by_account(org_id, provider, account_id)  # By account ID
```

### DomainEventRepository
```
find_by_org(org_id, skip, limit)  # Audit trail
find_by_entity(org_id, entity_id)  # All events for entity
find_by_type(org_id, event_type)
find_by_actor(org_id, actor_id)
get_event_chain(event_id)  # Follow causality links
```

**Use Case:** Event sourcing for audit/replay

### AuditLogRepository
```
find_by_org(org_id, skip, limit)
find_by_actor(org_id, actor_id)  # User activity
find_by_resource(org_id, resource_id)  # Resource history
find_by_action(org_id, action)  # Login, export, etc.
find_failures()  # Failed operations
```

**Use Case:** Compliance, security audit trail

### NotificationRepository
```
find_by_recipient(org_id, member_id, skip, limit)
find_unread(org_id, member_id)
count_unread(org_id, member_id)  # For badge
find_pending()  # Ready to send
find_failed()  # Failed, can retry

# State transitions
mark_as_read(notification_id)
mark_as_clicked(notification_id)
mark_as_sent(notification_id)
mark_as_delivered(notification_id)
mark_as_failed(notification_id, error)
```

---

## Usage Example

### Inject repositories into service

```python
from app.repositories import (
    ConversationRepository,
    MessageRepository,
    CustomerRepository,
)

class ConversationService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.customers = CustomerRepository(db)
    
    async def get_conversation_with_messages(self, org_id: str, conv_id: str):
        conversation = await self.conversations.read(conv_id)
        if not conversation:
            raise NotFound()
        
        messages = await self.messages.find_by_conversation(conv_id, skip=0, limit=50)
        customer = await self.customers.read(conversation.customer_id)
        
        return {
            "conversation": conversation,
            "messages": messages,
            "customer": customer,
        }
```

---

## MongoDB Integration

### Motor Connection
```python
# In app/core/database.py
from motor.motor_asyncio import AsyncIOMotorClient

db_client = AsyncIOMotorClient(settings.mongodb_url)
db = db_client[settings.mongodb_database]

# In repository
async def __init__(db: AsyncIOMotorDatabase):
    self.collection = db[collection_name]
```

### ObjectId Handling
```python
# Automatic in read/update/delete
from bson import ObjectId

# Converts "507f1f77bcf86cd799439011" ↔ ObjectId("507f1f77bcf86cd799439011")
```

---

## Index Strategy

**Repositories support:**
```python
async def create_index(keys, unique=False):
    """In-memory index creation"""
    return await self.collection.create_index(keys, unique=unique)
```

**Recommended indexes (created on startup):**

```python
# Identity
("organizations", [("slug", 1)], unique=True)
("members", [("organization_id", 1), ("user_id", 1)], unique=True)
("member_roles", [("member_id", 1), ("role_id", 1)], unique=True)

# Conversation
("customers", [("organization_id", 1), ("email", 1)])
("customer_identities", [("organization_id", 1), ("channel", 1), ("external_id", 1)], unique=True)
("conversations", [("organization_id", 1), ("status", 1), ("last_message_at", -1)])
("messages", [("conversation_id", 1), ("created_at", 1)])

# Integration
("integrations", [("organization_id", 1), ("provider", 1)])
("domain_events", [("organization_id", 1), ("event_type", 1), ("created_at", -1)])
("notifications", [("recipient_id", 1), ("read", 1), ("created_at", -1)])
```

---

## Next Steps

**Step 3: Service Layer**
- AuthService (login, register, tokens)
- OrganizationService (CRUD + multi-tenancy)
- ConversationService (create, assign, close)
- NotificationService (deliver notifications)
- EventPublisher (emit domain events)

**Step 4: API Routers**
- Auth endpoints
- Organization endpoints
- Conversation endpoints
- Customer endpoints
- Integration endpoints

---

## Statistics

**Repositories Created:** 18 specialized repositories
**Base CRUD Methods:** 10+ methods per repository
**Query Methods:** 50+ specialized queries
**Total Lines:** 1,337 production-ready lines

**Collections Covered:** All 13 collections
**Domains:** Identity, Conversation, Integration

---

**Repository Layer Complete** ✅  
**Ready for Step 3 (Services)** 🚀
