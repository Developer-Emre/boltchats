# 🔄 Migration Guide: Single-Tenant → Multi-Tenant (Slack-like B2B Platform)

## Overview

This guide explains how to migrate the existing Boltchats application from a single-tenant, room-based chat system to a multi-tenant, Slack-like B2B platform with workspaces, channels, and direct messages.

**Migration Duration:** ~2-3 hours for typical database size

---

## ✅ Pre-Migration Checklist

- [ ] **Backup Database** - Create a full backup before starting
  ```bash
  mongodump --uri="mongodb+srv://..." --out=./backup
  ```

- [ ] **Test on Staging** - Run migrations on staging environment first
  
- [ ] **Notify Users** - Schedule migration during low-traffic window
  
- [ ] **Code Deployed** - New API v2 should NOT be live yet (read-only mode)

---

## 🔄 Migration Steps (Order Matters!)

### STEP 1: Create New Collections & Indexes
**File:** `scripts/migration/001_create_new_collections.js`

```bash
mongosh --file scripts/migration/001_create_new_collections.js \
  --eval "const dbName = 'boltchats_db'"
```

**What it does:**
- Creates `workspaces`, `channels`, `direct_messages`, `invitations` collections
- Creates performance indexes on all collections
- Creates TTL index for invitation expiration

**Expected Output:**
```
✅ Created 'workspaces' collection
✅ Created 'channels' collection
✅ workspaces: index on slug (unique)
✅ channels: index on (workspace_id, name) (unique)
...
✨ [Migration 1] Complete!
```

**Time:** ~30 seconds

---

### STEP 2: Backfill User Workspaces
**File:** `scripts/migration/002_backfill_user_workspaces.js`

```bash
mongosh --file scripts/migration/002_backfill_user_workspaces.js \
  --eval "const dbName = 'boltchats_db'"
```

**What it does:**
- For each existing user, creates a default workspace (e.g., "alice's Workspace")
- Adds user as Owner of their workspace
- Adds workspace reference to user document

**Example:**
```
User: alice@company.com
  ↓
Creates Workspace: "alice's Workspace" (slug: alice-workspace)
  ↓
Updates User: adds workspace_id to user.workspaces array
```

**Expected Output:**
```
Found 42 users to process
✅ User alice: Created workspace 'alice's Workspace' (alice-workspace)
✅ User bob: Created workspace 'bob's Workspace' (bob-workspace)
...
✅ Workspaces created: 42
✅ Users updated: 42
✨ [Migration 2] Complete!
```

**Time:** ~1 minute (depending on user count)

---

### STEP 3: Migrate Rooms to Channels
**File:** `scripts/migration/003_migrate_rooms_to_channels.js`

```bash
mongosh --file scripts/migration/003_migrate_rooms_to_channels.js \
  --eval "const dbName = 'boltchats_db'"
```

**What it does:**
- For each Room, creates a corresponding Channel
- Assigns channel to room owner's workspace
- Preserves room metadata (name, description, members)
- Converts `is_private` → `type` (enum: public, private)
- Creates room-to-channel mapping for message migration

**Example:**
```
Old Room: "general" (is_private: false)
  ↓
New Channel: "general" (workspace_id: ws_1, type: "public")

Old Room: "private-team" (is_private: true)
  ↓
New Channel: "private-team" (workspace_id: ws_1, type: "private")
```

**Expected Output:**
```
Found 150 rooms to migrate
✅ Room 'general' → Channel (public)
✅ Room 'engineering' → Channel (public)
✅ Room 'secret' → Channel (private)
...
✅ Channels created: 150
✅ Mapping entries: 150
✨ [Migration 3] Complete!
```

**Time:** ~2 minutes (depending on room count)

**Note:** Creates temporary collection `migration_room_channel_map` for next step

---

### STEP 4: Add workspace_id and channel_id to Messages
**File:** `scripts/migration/004_add_workspace_to_messages.js`

```bash
mongosh --file scripts/migration/004_add_workspace_to_messages.js \
  --eval "const dbName = 'boltchats_db'"
```

**What it does:**
- For each Message, adds `workspace_id` and `channel_id`
- Uses room-to-channel mapping from STEP 3
- Renames old `room_id` to `old_room_id` (for reference)
- Adds new fields (threads, mentions, reactions, etc. as defaults)
- Updates channel message counts

**Example:**
```
Old Message:
  { _id: msg_1, room_id: room_123, content: "Hello" }
  ↓
New Message:
  {
    _id: msg_1,
    workspace_id: ws_1,
    channel_id: ch_123,
    old_room_id: room_123,  // for reference
    content: "Hello",
    thread_id: null,
    mentions: { user_ids: [], ... },
    reactions: {},
    ...
  }
```

**Expected Output:**
```
Found 45000 messages to process
   ... processed 1000/45000 messages
   ... processed 2000/45000 messages
...
✅ Messages updated: 45000
✅ Messages with workspace_id: 45000/45000
✅ Messages with channel_id: 45000/45000
✅ Updated message counts for 150 channels
✨ [Migration 4] Complete!
```

**Time:** ~2-5 minutes (depending on message count)

---

### STEP 5: Validate Migration
**File:** `scripts/migration/005_validate_migration.js`

```bash
mongosh --file scripts/migration/005_validate_migration.js \
  --eval "const dbName = 'boltchats_db'"
```

**What it does:**
- Checks all users have workspaces
- Verifies all channels have workspace_id
- Verifies all messages have workspace_id and channel_id
- Checks for duplicate workspace slugs
- Validates message-channel links
- Provides rollback instructions if needed

**Expected Output:**
```
[Check 1] Users have workspaces...
✅ All users have workspaces

[Check 2] Workspaces have members...
✅ All workspaces have members

...

======================================================================
MIGRATION VALIDATION SUMMARY
======================================================================

📊 Statistics:
   Users with workspaces: 42
   Total workspaces: 42
   Total channels: 150
   Total messages with workspace_id: 45000

✨ VALIDATION PASSED! Migration is complete and data is consistent.

📝 Next Steps:
   1. Deploy new API version (v2)
   2. Monitor for issues
   3. After 1 week: Deprecate v1 endpoints
   4. After 1 month: Delete rooms collection
```

**Time:** ~1 minute

---

## ✅ Post-Migration Steps

### 1. Verify API Works
```bash
# Test v2 API
curl http://localhost:8000/api/v2/users/me/workspaces \
  -H "Authorization: Bearer $TOKEN"

# Should return user's workspaces
{
  "workspaces": [
    {
      "workspace_id": "ws_1",
      "name": "alice's Workspace",
      "role": "owner"
    }
  ]
}
```

### 2. Test Frontend
- Clear browser cache
- Login and verify channels load
- Send a message
- Check message appears in all clients (WebSocket)

### 3. Monitor Logs
```bash
# Watch API logs for errors
docker logs boltchats-api -f

# Watch WebSocket logs
docker logs boltchats-ws -f
```

### 4. Run Tests
```bash
# Run migration validation tests
cd services/boltchats-api
pytest tests/integration/test_migration.py -v
```

---

## 🔄 Rollback (If Issues Occur)

If something goes wrong, you can rollback to the pre-migration state:

```bash
# Connect to MongoDB
mongosh <connection_string>

# Drop new collections (keeps old data intact)
db.workspaces.drop()
db.channels.drop()
db.direct_messages.drop()
db.invitations.drop()
db.migration_room_channel_map.drop()

# Restore users
db.users.updateMany({}, { $unset: { workspaces: 1 } })

# Restore messages
db.messages.updateMany(
  { old_room_id: { $exists: true } },
  {
    $rename: { old_room_id: 'room_id' },
    $unset: { workspace_id: 1, channel_id: 1 }
  }
)
```

**Result:** System will be back to pre-migration state. v1 API will continue working.

---

## 📊 Database Size After Migration

**Estimated Space Usage:**
```
Original Database:
  users collection: ~5 MB
  rooms collection: ~3 MB
  messages collection: ~200 MB
  Total: ~210 MB

After Migration (before cleanup):
  + workspaces: ~2 MB
  + channels: ~3 MB
  + direct_messages: ~0 MB (initially)
  + invitations: ~0 MB (initially)
  + migration_room_channel_map: ~1 MB (temporary)
  = Additional: ~6 MB

Total After Migration: ~216 MB

After Cleanup (drop rooms collection):
  Total: ~213 MB
```

---

## ⚡ Performance Impact

**Read Performance:** ✅ IMPROVED
- New indexes on `workspace_id` make queries faster
- Composite indexes on `(workspace_id, channel_id)` optimize message queries

**Write Performance:** ➖ NEUTRAL
- Similar number of writes
- Slightly more fields per document

**Index Size:** ~15 MB (acceptable)

---

## 🎯 Timeline

| Phase | Duration | Task |
|-------|----------|------|
| Backup | 5 min | Create full database backup |
| Step 1 | 1 min | Create collections & indexes |
| Step 2 | 1 min | Backfill user workspaces |
| Step 3 | 2 min | Migrate rooms to channels |
| Step 4 | 3 min | Add workspace_id to messages |
| Step 5 | 1 min | Validate migration |
| Test | 10 min | Verify API and frontend |
| **TOTAL** | **~25 min** | Complete migration |

---

## 🆘 Troubleshooting

### Issue: "Script fails at Step 2"
**Cause:** Some users already have workspaces (partial migration)
**Solution:** Check if workspaces collection has data. If so, you may need to restart from backup.

### Issue: "Messages don't have workspace_id after Step 4"
**Cause:** room_id values don't match mapping (data corruption?)
**Solution:** 
  1. Check `migration_room_channel_map` collection
  2. Verify room_ids in messages collection
  3. If issue persists, rollback and contact support

### Issue: "Performance degraded after migration"
**Cause:** Indexes not created properly
**Solution:**
  ```bash
  mongosh <connection_string>
  db.messages.getIndexes()  # Verify indexes exist
  db.messages.reIndex()     # Rebuild indexes
  ```

### Issue: "Duplicate slugs error in Step 1"
**Cause:** Workspace slugs not unique
**Solution:** This is caught in validation Step 5. Check for naming conflicts.

---

## 📝 Monitoring After Migration

**Key Metrics to Watch:**

```
1. API Latency (should stay same or improve)
   GET /api/v2/channels → should be < 100ms

2. Message Throughput (same as before)
   POST /api/v2/channels/{id}/messages → should be < 200ms

3. WebSocket Connections (should not increase)
   Active WS connections in boltchats-ws

4. Error Rate (should be 0%)
   Monitor logs for 5xx errors
```

---

## ✅ Sign-Off Checklist

Before considering migration complete:

- [ ] All 5 migration scripts completed successfully
- [ ] Validation script shows ✅ PASSED
- [ ] API tests passing
- [ ] Frontend loads without errors
- [ ] Can send/receive messages
- [ ] WebSocket events firing correctly
- [ ] No 5xx errors in logs (24 hours)
- [ ] Performance metrics stable
- [ ] Users report no issues

---

## 📞 Support

If you encounter issues:

1. Check logs: `docker logs boltchats-api`
2. Run validation: `mongosh --file scripts/migration/005_validate_migration.js`
3. Use rollback procedure above
4. Contact development team

---

## 🎓 What Changed

### Before (v1 - Single Tenant)
```
User → Creates Rooms → Sends Messages
One global database for all users
```

### After (v2 - Multi Tenant)
```
User → Creates Workspace → Creates Channels → Sends Messages
Each workspace is isolated (workspace_id on every document)
Supports multiple users and organizations
```

---

## Next Steps

1. **API v2 Development**
   - New endpoints with workspace context
   - JWT claims include workspace_id
   - Middleware verifies workspace membership

2. **Frontend Updates**
   - Workspace switcher UI
   - Channel sidebar
   - DM panel
   - Invitation system

3. **Onboarding Flow**
   - Signup
   - Email verification
   - Workspace creation or invitation acceptance
   - Default channels (#general, #random)

