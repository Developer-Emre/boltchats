# Member ID Flow in Authentication

## Overview

member_id, bir kullanıcının belirli bir organizasyon içindeki üyeliğini temsil eder. Bir kullanıcı birden fazla organizasyonda member olabilir.

---

## member_id Akışı

### 1. Registration

```
User Input
  ↓
POST /auth/register
  ↓
AuthenticationService.register()
  ├─ Create User
  └─ Create Member(organization_id="default", user_id=user.id, status=ACTIVE)
       └─ Returns member_id
  ↓
TokenService.create_tokens(member_id)
  └─ Includes in access token payload: "member_id": member_id
  ↓
Response: {access_token, refresh_token, user_id, member_id, org_id}
```

### 2. Login

```
POST /auth/login
  ↓
AuthenticationService.login()
  ├─ Find User by email
  ├─ Verify password
  ├─ Find Members for user
  ├─ Filter for ACTIVE only
  └─ Extract member from first active membership
       └─ member.id used for token
  ↓
TokenService.create_tokens(member_id)
  └─ Includes in access token payload: "member_id": member_id
  ↓
Response: {access_token, refresh_token, user_id, member_id, org_id}
```

### 3. Access Token Usage

```
GET /api/v1/protected
  ├─ Authorization: Bearer <access_token>
  ↓
get_current_user dependency
  ├─ Decode token
  ├─ Verify signature
  └─ Extract payload: {user_id, org_id, member_id, roles, type, ...}
  ↓
Handler receives: current_user = {
  "user_id": "...",
  "org_id": "...",
  "member_id": "...",
  "roles": [...],
  "type": "access"
}
```

### 4. Token Refresh

```
POST /auth/refresh
  ├─ Receive refresh_token
  ├─ Extract user_id from refresh_token (without verification)
  ↓
AuthenticationService.get_active_member(user_id)
  ├─ Find all members for user_id
  ├─ Filter for ACTIVE only
  └─ Return first active member
       └─ member.id used for new access token
  ↓
TokenService.create_access_token_from_refresh(member_id)
  └─ New access token includes: "member_id": member_id
  ↓
Response: {access_token, refresh_token, user_id, member_id, org_id}
```

### 5. Protected Endpoint with member_id

```
Handler can access:
  current_user["member_id"]
  current_user["user_id"]
  current_user["org_id"]
  current_user["roles"]
```

---

## Token Payload Structure

### Access Token
```json
{
  "user_id": "6a6f23771829836c96b5e7e3",      // User's unique ID
  "org_id": "default",                         // Organization ID
  "member_id": "6a6f23771829836c96b5e7e4",   // Member ID (user in this org)
  "roles": ["member", "viewer"],               // Member's roles in org
  "type": "access",
  "iat": 1785668491,
  "exp": 1785670291                            // 30 minutes from iat
}
```

### Refresh Token
```json
{
  "user_id": "6a6f23771829836c96b5e7e3",      // User ID
  "org_id": "default",                         // Organization ID
  "type": "refresh",                           // ⚠️ No member_id (fetched on refresh)
  "iat": 1785668491,
  "exp": 1786273291                            // 7 days from iat
}
```

---

## Key Design Decisions

### 1. Why member_id in Access Token?
- ✅ Used to check permissions in organization context
- ✅ Enables role-based access control (RBAC)
- ✅ Identifies which membership is being used

### 2. Why NO member_id in Refresh Token?
- ✅ Keeps refresh token lightweight (smaller size)
- ✅ member_id can change (user removed from org)
- ✅ Refresh token doesn't need org-specific context
- ✅ member_id fetched fresh from DB on each refresh

### 3. Why Status Check?
- ✅ Prevents SUSPENDED/INACTIVE/ARCHIVED members from accessing
- ✅ Immediate revocation when member status changes
- ✅ Security: disable member immediately without token invalidation

---

## Member Status Values

```python
class MemberStatus(str, Enum):
    ACTIVE = "active"           # ✅ Can login
    SUSPENDED = "suspended"     # ❌ Cannot login
    INACTIVE = "inactive"       # ❌ Cannot login
    ARCHIVED = "archived"       # ❌ Cannot login
```

Login accepts ONLY: `ACTIVE`

---

## Multi-Organization Support

If user is member of multiple organizations:

```python
# Example: User in 3 organizations
[
  Member(id="mem1", organization_id="org_1", user_id="user1", status=ACTIVE),
  Member(id="mem2", organization_id="org_2", user_id="user1", status=ACTIVE),
  Member(id="mem3", organization_id="org_3", user_id="user1", status=SUSPENDED)
]

# Login selects first ACTIVE:
login() → returns member_id="mem1" (org_1)

# Future: Add org_id parameter to login for explicit org selection
POST /auth/login
{
  "email": "user@example.com",
  "password": "...",
  "organization_id": "org_2"  // Explicit org choice
}
```

Currently: always picks first active member (default org).

---

## API Examples

### Register with member_id

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "organization_name": "Acme Corp"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "6a6f23771829836c96b5e7e3",
  "member_id": "6a6f23771829836c96b5e7e4",
  "organization_id": "default"
}
```

### Get /me with member_id

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "user_id": "6a6f23771829836c96b5e7e3",
  "email": "",
  "full_name": "",
  "organization_id": "default",
  "workspace_id": "",
  "member_id": "6a6f23771829836c96b5e7e4",
  "roles": ["member"],
  "permissions": []
}
```

### Refresh preserves member_id

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ..."
  }'
```

**Response:**
```json
{
  "access_token": "eyJ...",          // NEW with member_id preserved
  "refresh_token": "eyJ...",         // Same refresh token
  "token_type": "bearer",
  "expires_in": 1800,
  "user_id": "6a6f23771829836c96b5e7e3",
  "member_id": "6a6f23771829836c96b5e7e4",  // ✅ From DB lookup
  "organization_id": "default"
}
```

---

## Using member_id in Endpoints

```python
from fastapi import Depends
from app.core.security import get_current_user

@router.get("/api/v1/conversations")
async def list_conversations(
    current_user = Depends(get_current_user)
):
    """Access organization's conversations"""
    user_id = current_user["user_id"]
    member_id = current_user["member_id"]
    org_id = current_user["org_id"]
    
    # Example: Find conversations for this member's organization
    conversations = await conversation_service.find_many({
        "organization_id": org_id
    })
    
    # Or: Use member_id for member-specific operations
    permissions = await permission_service.get_member_permissions(member_id)
    
    return {"conversations": conversations}
```

---

## Testing member_id Flow

```bash
#!/bin/bash

# 1. Register
RESP=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Pass123!",
    "full_name": "Test",
    "organization_name": "Test"
  }')

MEMBER_ID=$(echo "$RESP" | jq -r '.member_id')
ACCESS=$(echo "$RESP" | jq -r '.access_token')
REFRESH=$(echo "$RESP" | jq -r '.refresh_token')

echo "Registered member_id: $MEMBER_ID"

# 2. Check access token contains member_id
# (Decode and verify payload)

# 3. Get /me
curl -s -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS" | jq '.member_id'

# 4. Refresh and verify member_id preserved
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}" | jq '.member_id'
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| member_id empty in response | Not in TokenResponse schema | Add to schema |
| member_id null in access token | Passed as None | Pass as string (empty "") |
| member_id lost after refresh | Fetched from refresh token (has none) | Fetch from DB in router |
| User can't login (suspended) | Status not checked | Filter for ACTIVE |
| Different member_id each refresh | First member always picked | Use consistent member selection |

---

## Future Improvements

- [ ] Allow user to select which org to login to (multi-tenant)
- [ ] Cache member_id in Redis during refresh (less DB hits)
- [ ] Include member roles in access token (currently refetched on each request)
- [ ] Add member_id to audit logs
- [ ] Support member workspace/team selection during login
- [ ] Implement organization switching without re-login

---

## Summary

✅ **member_id flow is now complete and correct:**
- Registered with first Active member
- Included in access token payload
- Preserved through token refresh (fetched from DB)
- Accessible in all protected endpoints
- Prevents suspended members from accessing
- Ready for multi-organization support

