# 🔄 Boltchats → B2B Platform Migration Plan

## 📊 Current State vs Target State

### CURRENT (Single Tenant - Room Based)
```
User Collection:
  - _id, username, email, password
  - No workspace reference

Room Collection:
  - _id, name, owner_id, member_ids, is_private

Message Collection:
  - _id, room_id, sender_id, content
```

### TARGET (Multi-Tenant - Channel Based)
```
User Collection:
  - _id, username, email, password
  - workspaces: [ { workspace_id, role, joined_at } ]

Workspace Collection (NEW):
  - _id, name, slug, owner_id, members

Channel Collection (renamed from Room):
  - _id, workspace_id, name, type (public/private/direct/shared)
  - owner_id, members

DirectMessage Collection (NEW):
  - _id, workspace_id, participants, created_by

Message Collection (updated):
  - _id, workspace_id, channel_id (or dm_id), sender_id

Invitation Collection (NEW):
  - _id, workspace_id, invited_email, code, status
```

---

## 🎯 Migration Strategy

### Approach: Dual Write Phase
```
Week 1-2: Deploy v2 API alongside v1 (both work)
Week 3: Migrate data in background
Week 4: Validate migration, test thoroughly
Week 5: Cutover to v2, keep v1 as fallback
Week 6: Deprecate v1
```

---

## 📝 Detailed Migration Steps

### STEP 1: Create New Collections (Non-Destructive)
```
✅ Create "workspaces" collection
✅ Create "channels" collection (copy of rooms initially)
✅ Create "direct_messages" collection
✅ Create "invitations" collection
✅ Keep "rooms" collection (for now)
```

### STEP 2: Backfill User Workspaces
```
For each user:
  ├─ Create default workspace "{username}'s Workspace"
  ├─ Add user to workspace with role = "owner"
  └─ Add to user.workspaces array
```

### STEP 3: Migrate Rooms → Channels
```
For each room:
  ├─ Create corresponding channel in "channels" collection
  ├─ Copy: name, description, owner_id, member_ids
  ├─ Add: workspace_id (from user's default workspace)
  ├─ Set: type = "public" if !is_private else "private"
  └─ Map old room_id to new channel_id
```

### STEP 4: Migrate Messages
```
For each message:
  ├─ Add workspace_id (from channel's workspace_id)
  ├─ Rename room_id → channel_id
  └─ Keep everything else same
```

### STEP 5: Deploy v2 API
```
✅ New models with workspace_id
✅ New endpoints with /api/v2 prefix
✅ Middleware: Extract workspace_id from JWT or header
✅ Backward compat: v1 endpoints still work (but deprecated)
```

### STEP 6: Cutover & Cleanup
```
✅ Verify all data migrated correctly
✅ Point frontend to v2
✅ Monitor for issues
✅ After 1 week: Archive v1 endpoints
✅ After 1 month: Delete rooms collection
```

---

## 🗄️ Migration Scripts

### Script 1: Create New Collections & Indexes
File: `migration/001_create_new_collections.js`

### Script 2: Backfill User Workspaces
File: `migration/002_backfill_user_workspaces.js`

### Script 3: Migrate Rooms to Channels
File: `migration/003_migrate_rooms_to_channels.js`

### Script 4: Add workspace_id to Messages
File: `migration/004_add_workspace_to_messages.js`

### Script 5: Validation & Rollback
File: `migration/005_validate_migration.js`

---

## ⏱️ Timeline

| Week | Task | Owner |
|------|------|-------|
| 1 | Write migration scripts | Backend |
| 1 | Test on staging DB | Backend |
| 2 | Deploy v2 API (read-only) | Backend |
| 2-3 | Run migration on staging | Backend |
| 3 | Update tests | QA |
| 3-4 | Deploy v2 API (full) | Backend |
| 4 | Cutover frontend to v2 | Frontend |
| 5 | Monitor, fix bugs | DevOps |
| 6+ | Cleanup, deprecate v1 | Backend |

---

## ✅ Validation Checklist

- [ ] All users have workspace
- [ ] All rooms migrated to channels
- [ ] All messages have workspace_id
- [ ] No data loss
- [ ] Message count matches
- [ ] Member counts match
- [ ] Index creation successful
- [ ] Query performance acceptable
- [ ] v2 API tests passing
- [ ] Backward compat working
- [ ] Frontend loads without errors

