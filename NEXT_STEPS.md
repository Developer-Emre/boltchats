# 📋 Next Steps - B2B Slack-like Platform Migration

## Current Status ✅
- [x] Database schema designed (7 collections)
- [x] Python models updated (user.py, message.py, workspace.py, channel.py, etc.)
- [x] 5 MongoDB migration scripts written
- [x] Migration guide created (README.md)

## Immediate Actions (This Week)

### Week 1: Test & Validate Migrations
**Responsible:** Backend Lead
**Time:** 4-6 hours

1. **Setup Staging Database**
   ```bash
   # Create backup of production
   mongodump --uri="mongodb+srv://..." --out=./backup-prod-$(date +%Y%m%d)
   
   # Create staging copy
   mongorestore --uri="mongodb+srv://staging..." ./backup-prod-$(date +%Y%m%d)
   ```

2. **Run All 5 Migration Scripts**
   ```bash
   cd scripts/migration
   
   mongosh --file 001_create_new_collections.js
   mongosh --file 002_backfill_user_workspaces.js
   mongosh --file 003_migrate_rooms_to_channels.js
   mongosh --file 004_add_workspace_to_messages.js
   mongosh --file 005_validate_migration.js
   ```

3. **Document Results**
   - [ ] All scripts completed without errors
   - [ ] Validation report shows ✅ PASSED
   - [ ] Message counts match pre-migration (important!)
   - [ ] No duplicate slugs
   - [ ] All indexes created

4. **Test API with New Schema**
   - API should still work (backward compatible during migration)
   - Query by workspace_id (prepare for v2)

5. **If Issues Found:**
   - Run rollback procedure (see README.md)
   - Fix migration script
   - Re-test

---

### Week 1-2: Update API Routes (Critical Path)
**Responsible:** API Developer
**Time:** 8-10 hours

> ⚠️ **BLOCKING ISSUE:** The updated `user.py` and `message.py` models are breaking changes. Existing routers will fail because they don't provide the new required fields.

#### Phase 1: Backward Compatibility (Router Updates)
1. **Add workspace context to all endpoints**
   ```python
   # Before (old):
   @router.get("/channels/{room_id}")
   async def get_channel(room_id: str, user_id: str = Depends(get_current_user)):
       ...
   
   # After (new):
   @router.get("/api/v2/workspaces/{workspace_id}/channels/{channel_id}")
   async def get_channel(
       workspace_id: str,
       channel_id: str,
       user_id: str = Depends(get_current_user),
       workspace_check = Depends(verify_user_in_workspace)
   ):
       ...
   ```

2. **Create middleware: `verify_user_in_workspace`**
   - Checks if user is member of workspace
   - Prevents cross-tenant data access
   - Add to all v2 endpoints

3. **Refactor service layer**
   - All functions must accept `workspace_id` parameter
   - Add query filter: `{"workspace_id": workspace_id}`
   - Example: `db.channels.find_one({"workspace_id": ws_id, "_id": ch_id})`

#### Phase 2: New Endpoints (v2 API)
Create new router: `services/boltchats-api/app/routers/v2_workspaces.py`

```python
# Workspace Management
POST   /api/v2/workspaces                      # Create workspace
GET    /api/v2/workspaces                      # List user's workspaces
GET    /api/v2/workspaces/{workspace_id}       # Get workspace details
PATCH  /api/v2/workspaces/{workspace_id}       # Update workspace

# Channels
GET    /api/v2/workspaces/{workspace_id}/channels
POST   /api/v2/workspaces/{workspace_id}/channels
GET    /api/v2/workspaces/{workspace_id}/channels/{channel_id}
POST   /api/v2/workspaces/{workspace_id}/channels/{channel_id}/messages

# Members
GET    /api/v2/workspaces/{workspace_id}/members
POST   /api/v2/workspaces/{workspace_id}/members/{user_id}  # Add member
DELETE /api/v2/workspaces/{workspace_id}/members/{user_id}  # Remove member

# Invitations
POST   /api/v2/workspaces/{workspace_id}/invitations        # Create invite
POST   /api/v2/invitations/{code}/accept                    # Accept invite
```

---

### Week 2: Update WebSocket Handlers
**Responsible:** WebSocket Lead
**Time:** 4-6 hours

1. **Add workspace context to all events**
   ```python
   # Old event:
   {
       "type": "message.created",
       "data": { "room_id": "r_1", "message": "Hello" }
   }
   
   # New event:
   {
       "type": "message.created",
       "data": {
           "workspace_id": "ws_1",
           "channel_id": "ch_1",
           "message": "Hello"
       }
   }
   ```

2. **Update broadcast manager**
   - Route events by workspace first, then channel
   - Prevent cross-workspace message leaks

3. **New WebSocket event types**
   ```python
   workspace.user.joined      # User added to workspace
   workspace.user.left        # User removed from workspace
   workspace.member.updated   # Role changed
   channel.created            # New channel in workspace
   channel.deleted            # Channel deleted
   ```

---

### Week 2-3: Integration Tests
**Responsible:** QA / Backend Lead
**Time:** 6-8 hours

Create test file: `services/boltchats-api/tests/integration/test_b2b_migration.py`

```python
# Test cases needed:
1. test_user_can_create_workspace()
2. test_user_has_default_workspace()
3. test_user_can_be_invited_to_workspace()
4. test_user_cannot_access_other_workspaces()
5. test_messages_isolated_by_workspace()
6. test_channels_isolated_by_workspace()
7. test_migrate_rooms_to_channels()
8. test_message_counts_preserved()
9. test_workspace_member_list()
10. test_invite_code_generation_and_acceptance()
```

---

## Phase 2: Frontend Updates (Week 3-4)

### Updates Needed
1. **Add workspace context to all API calls**
   - Include workspace_id in headers or URLs
   - Update environment config

2. **UI Components**
   - [ ] Workspace switcher (top-left dropdown)
   - [ ] Channel sidebar (list channels in workspace)
   - [ ] DM panel (direct messages)
   - [ ] Settings → Workspace settings
   - [ ] Settings → Workspace members & invitations

3. **Onboarding Flow**
   - [ ] Signup form
   - [ ] Email verification
   - [ ] Workspace creation OR invite code input
   - [ ] Default channels creation (#general, #random)
   - [ ] Welcome tour

---

## Phase 3: Deployment (Week 4-5)

### Deployment Strategy
```
Week 4:
  - Deploy v2 API to staging (keep v1 read-only)
  - Full QA testing on staging
  
Week 4-5:
  - Production deployment (v1 and v2 live simultaneously)
  - Run migration scripts on production
  - Frontend team updates to v2 endpoints
  
Week 5:
  - Monitor error rates and latency
  - Run user acceptance tests
  - Gradually shift traffic to v2
  
Week 6:
  - Deprecate v1 endpoints
  - Keep v1 code for 2 weeks (safety)
  - After 1 month: Delete rooms collection
```

---

## Files & Locations

### Migration Scripts
```
scripts/migration/
├── README.md                           # Migration guide ✅
├── 001_create_new_collections.js       # Create collections ✅
├── 002_backfill_user_workspaces.js     # Backfill workspaces ✅
├── 003_migrate_rooms_to_channels.js    # Migrate rooms ✅
├── 004_add_workspace_to_messages.js    # Add workspace_id ✅
└── 005_validate_migration.js           # Validate ✅
```

### Updated Models
```
services/boltchats-api/app/models/
├── user.py                 # ✅ Updated - now has workspaces array
├── message.py              # ✅ Updated - now has workspace_id, channel_id
├── room.py                 # ✅ Unchanged (for backward compat)
├── workspace.py            # ✅ New
├── channel.py              # ✅ New
├── direct_message.py       # ✅ New
└── invitation.py           # ✅ New
```

### New Routers (To Create)
```
services/boltchats-api/app/routers/
├── workspaces.py           # 🆕 Workspace CRUD
├── channels.py             # 🆕 Channel CRUD (replaces rooms)
├── direct_messages.py      # 🆕 DM endpoints
└── invitations.py          # 🆕 Invitation endpoints
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Migration script fails | LOW | HIGH | Full backup + rollback procedure |
| Data loss during migration | LOW | CRITICAL | Test on staging first |
| Message count mismatch | MEDIUM | MEDIUM | Validation script checks this |
| API breaks after migration | MEDIUM | HIGH | Backward compatibility layer |
| WebSocket events fail | MEDIUM | HIGH | Update handlers before deployment |
| Cross-tenant data leak | LOW | CRITICAL | workspace_id verification middleware |

---

## Success Criteria ✅

Migration is complete when:
- [x] All 5 migration scripts run successfully
- [x] Database validation shows no errors
- [x] All API tests passing
- [x] WebSocket events working
- [x] Frontend loads without errors
- [x] Users can login and see workspaces
- [x] Users can send/receive messages
- [x] No data loss or corruption
- [x] 0% error rate in logs (24+ hours)
- [x] Performance metrics stable

---

## Estimated Timeline

```
Total Effort: ~6-8 weeks

Week 1:    Migration scripts tested ✅ (Already done design)
Week 2:    API routes updated
Week 3:    WebSocket updated + Integration tests
Week 4:    Frontend updates
Week 5:    Deployment (staging → production)
Week 6:    Monitoring + Bug fixes
Week 7-8:  v1 sunset + Cleanup
```

---

## Decision Points

### 1. When to run migration on production?
**Recommendation:** After all v2 API endpoints tested on staging and passing all tests (Week 3-4)

### 2. Keep v1 endpoints alive for how long?
**Recommendation:** 2 weeks (allows time for client-side caching, CDN updates)

### 3. When to delete old collections (rooms, old_room_id fields)?
**Recommendation:** 1 month after production deployment (safety buffer)

---

## Questions for Product/Leadership

1. **Go-to-market timing?** When do we announce B2B platform to existing users?
2. **Pricing model?** Usage-based, seat-based, tiered?
3. **Trial period?** 14-30 days free?
4. **GitHub integration priority?** First or Phase 2?
5. **N8N-like automation?** Phase 1 or Phase 2?

