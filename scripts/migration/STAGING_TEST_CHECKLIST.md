# 🚀 Migration Staging Test Checklist

**Date:** 2026-07-28  
**Status:** Ready to Test  
**Environment:** Staging  

---

## Pre-Migration Setup

### Prerequisites
- [ ] MongoDB staging instance running
- [ ] Connection string: `mongodb+srv://...`
- [ ] Database name: `boltchats_staging`
- [ ] Full database backup available
- [ ] All Python services can access DB

### API Version Status
- [ ] v1 API (old room-based) is **LIVE and WORKING**
- [ ] v2 API (new workspace-based) is **DEPLOYED but DISABLED** (read-only mode)
- [ ] All v2 endpoints return 503 Service Unavailable until migration completes
- [ ] No user traffic on v2 endpoints

---

## Migration Execution

### Step 1: Pre-Flight Checks
```bash
# Verify connection to staging DB
mongosh --uri="mongodb+srv://..." --eval "db.adminCommand('ping')"
# Expected: { "ok" : 1 }

# Backup database
mongodump --uri="mongodb+srv://..." --out=./backup-$(date +%Y%m%d)
# Verify backup completed successfully
```

- [ ] MongoDB connection working
- [ ] Database backup created successfully

### Step 2: Run Migration Scripts (In Order)

**IMPORTANT:** Each script must complete before next one starts

#### Step 2.1: Create Collections & Indexes
```bash
mongosh --uri="mongodb+srv://..." \
  --eval "const dbName = 'boltchats_staging'" \
  --file scripts/migration/001_create_new_collections.js
```

Expected Output:
```
✅ Created 'workspaces' collection
✅ Created 'channels' collection
✅ Created 'direct_messages' collection
✅ Created 'invitations' collection
✅ workspaces: index on slug (unique)
... (more indexes)
✨ [Migration 1] Complete!
```

**Status:** [ ] COMPLETE  
**Time:** ~30s  
**Issues:** ___________

---

#### Step 2.2: Backfill User Workspaces
```bash
mongosh --uri="mongodb+srv://..." \
  --eval "const dbName = 'boltchats_staging'" \
  --file scripts/migration/002_backfill_user_workspaces.js
```

Expected Output:
```
Found X users to process
✅ User alice: Created workspace 'alice's Workspace' (alice-workspace)
✅ User bob: Created workspace 'bob's Workspace' (bob-workspace)
...
✅ Workspaces created: X
✅ Users updated: X
✨ [Migration 2] Complete!
```

**Status:** [ ] COMPLETE  
**Time:** ~1 min  
**Users Processed:** ___________  
**Issues:** ___________

---

#### Step 2.3: Migrate Rooms to Channels
```bash
mongosh --uri="mongodb+srv://..." \
  --eval "const dbName = 'boltchats_staging'" \
  --file scripts/migration/003_migrate_rooms_to_channels.js
```

Expected Output:
```
Found X rooms to migrate
✅ Room 'general' → Channel (public)
✅ Room 'engineering' → Channel (public)
✅ Room 'secret' → Channel (private)
...
✅ Channels created: X
✅ Mapping entries: X
✨ [Migration 3] Complete!
```

**Status:** [ ] COMPLETE  
**Time:** ~2 min  
**Rooms Migrated:** ___________  
**Issues:** ___________

---

#### Step 2.4: Add workspace_id to Messages
```bash
mongosh --uri="mongodb+srv://..." \
  --eval "const dbName = 'boltchats_staging'" \
  --file scripts/migration/004_add_workspace_to_messages.js
```

Expected Output:
```
Found X messages to process
   ... processed 1000/X messages
   ... processed 2000/X messages
...
✅ Messages updated: X
✅ Messages with workspace_id: X/X
✅ Messages with channel_id: X/X
✅ Updated message counts for X channels
✨ [Migration 4] Complete!
```

**Status:** [ ] COMPLETE  
**Time:** ~3-5 min  
**Messages Updated:** ___________  
**Issues:** ___________

---

#### Step 2.5: Validate Migration
```bash
mongosh --uri="mongodb+srv://..." \
  --eval "const dbName = 'boltchats_staging'" \
  --file scripts/migration/005_validate_migration.js
```

Expected Output:
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
   Users with workspaces: X
   Total workspaces: X
   Total channels: X
   Total messages with workspace_id: X

✨ VALIDATION PASSED! Migration is complete and data is consistent.
```

**Status:** [ ] COMPLETE  
**Validation:** [ ] PASSED ✅ / [ ] FAILED ❌  
**Issues:** ___________

---

## Post-Migration Testing

### 1. API Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "service": "boltchats-api"}
```
- [ ] Health endpoint working

### 2. List Workspaces
```bash
curl http://localhost:8000/api/v2/workspaces \
  -H "Authorization: Bearer $TOKEN"
# Expected: { "items": [...], "next_cursor": null }
```
- [ ] API returns user's workspaces

### 3. List Channels
```bash
curl http://localhost:8000/api/v2/workspaces/{id}/channels \
  -H "Authorization: Bearer $TOKEN"
# Expected: { "items": [...], "next_cursor": null }
```
- [ ] API returns workspace's channels

### 4. Send Message to Channel
```bash
curl -X POST http://localhost:8000/api/v2/workspaces/{ws_id}/channels/{ch_id}/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message"}'
# Expected: { "id": "...", "sender_id": "...", ... }
```
- [ ] Message creation works

### 5. Fetch Message History
```bash
curl http://localhost:8000/api/v2/workspaces/{ws_id}/channels/{ch_id}/messages \
  -H "Authorization: Bearer $TOKEN"
# Expected: { "items": [...], "next_cursor": null }
```
- [ ] Message history retrieval works

---

### 6. WebSocket Connection
```bash
# Connect to WebSocket
wscat -c ws://localhost:8001 \
  -H "Authorization: Bearer $TOKEN"

# Should connect and authenticate successfully
```
- [ ] WebSocket connection works

### 7. Run Integration Tests
```bash
cd services/boltchats-api
pytest tests/integration/test_migration.py -v
```

Expected results:
```
test_users_have_workspaces PASSED
test_workspaces_exist PASSED
test_channels_exist PASSED
test_messages_have_workspace_id PASSED
test_messages_have_channel_id PASSED
test_channel_message_counts_updated PASSED
test_workspace_member_consistency PASSED
test_channel_member_consistency PASSED
test_message_sender_consistency PASSED
...
======================== X passed in 10.23s ==========================
```

- [ ] All integration tests PASSED

### 8. Frontend Testing
- [ ] Login with staging credentials
- [ ] See workspace switcher
- [ ] See list of channels
- [ ] Send message to channel
- [ ] Message appears instantly (WebSocket)
- [ ] Logout and login again - data persists
- [ ] No console errors

- [ ] Frontend works correctly

---

## Performance Validation

### Database Performance
```bash
# Check index performance
mongosh --uri="mongodb+srv://..." --eval "
  db.messages.aggregate([
    { \$match: { workspace_id: 'ws_1', channel_id: 'ch_1' } },
    { \$sort: { created_at: -1 } },
    { \$limit: 50 }
  ]).explain('executionStats')
"
# Should use an index (not COLLSCAN)
```

- [ ] Message query uses index (no COLLSCAN)
- [ ] Response time < 100ms
- [ ] API latency stable

---

## Rollback Plan (If Needed)

If migration failed at any step, execute rollback:

```bash
# 1. Connect to MongoDB
mongosh --uri="mongodb+srv://..."

# 2. Drop new collections
db.workspaces.drop()
db.channels.drop()
db.direct_messages.drop()
db.invitations.drop()
db.migration_room_channel_map.drop()

# 3. Restore users
db.users.updateMany({}, { $unset: { workspaces: 1 } })

# 4. Restore messages
db.messages.updateMany(
  { old_room_id: { $exists: true } },
  {
    $rename: { old_room_id: 'room_id' },
    $unset: { workspace_id: 1, channel_id: 1 }
  }
)

# 5. Verify
db.users.findOne()  # Should NOT have workspaces field
db.messages.findOne()  # Should have room_id, not channel_id
```

- [ ] Rollback executed if needed
- [ ] Data verified post-rollback

---

## Sign-Off

### Migration Manager
- Name: ___________
- Date: ___________
- Signature: ___________

### QA Lead
- Name: ___________
- Date: ___________
- Signature: ___________

### DevOps
- Name: ___________
- Date: ___________
- Signature: ___________

---

## Issues & Resolutions

| Issue | Step | Status | Resolution |
|-------|------|--------|-----------|
| | | [ ] PENDING | |
| | | [ ] RESOLVED | |
| | | [ ] PENDING | |
| | | [ ] RESOLVED | |

---

## Notes

___________________________________________________________________________

___________________________________________________________________________

___________________________________________________________________________

---

## Success Criteria ✅

All items must be checked before marking migration as COMPLETE:

- [ ] All 5 migration scripts ran successfully
- [ ] Migration validation script PASSED
- [ ] API health check working
- [ ] All integration tests PASSED
- [ ] Frontend working correctly
- [ ] WebSocket connection working
- [ ] Database performance acceptable
- [ ] No errors in logs
- [ ] All sign-offs collected

---

## Timeline Summary

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| Backup | 5 min | | |
| Step 1 | 1 min | | |
| Step 2 | 1 min | | |
| Step 3 | 2 min | | |
| Step 4 | 3 min | | |
| Step 5 | 1 min | | |
| Testing | 15 min | | |
| **TOTAL** | **~28 min** | | |

---

**Generated:** 2026-07-28  
**Template Version:** 1.0  
**Last Updated:** 2026-07-28
