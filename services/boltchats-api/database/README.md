# Database Setup Guide

## Quick Start

### Option 1: Using Python CLI (Recommended)

```bash
# Run all migrations (create collections + indexes)
python -m app.cli.db migrate

# Seed initial data for organization
python -m app.cli.db seed <org_id>

# Reset seeded data
python -m app.cli.db reset <org_id>

# Rollback all migrations (DESTRUCTIVE)
python -m app.cli.db rollback
```

### Option 2: Using Mongosh Script

```bash
# Connect to MongoDB and run initialization script
mongosh < database/init.mongosh

# Or manually in Mongosh shell:
use boltchats
load("database/init.mongosh")
```

## Migrations

Database migrations are handled by Python scripts in `app/db/migrations.py`.

### Migration Classes

1. **CreateCollectionsMigration** (v1)
   - Creates all MongoDB collections
   - Handles already-existing collections gracefully

2. **CreateIndexesMigration** (v2)
   - Creates performance indexes for all collections
   - Single-field, compound, and unique indexes

## Indexes Created

### Identity Domain
- `users`: email (unique)
- `organizations`: slug (unique)
- `members`: (organization_id, workspace_id), (organization_id, user_id, unique), email
- `roles`: implicit on organization_id + name

### Conversation Domain
- `customers`: (organization_id, email)
- `customer_identities`: (customer_id, provider, unique), (provider, external_id)
- `conversations`: 
  - (organization_id, customer_id, channel)
  - (organization_id, status)
  - (organization_id, assigned_to)
  - created_at
- `messages`: 
  - (conversation_id, created_at DESC)
  - sender_id
  - created_at
- `labels`: (organization_id, name, unique)
- `drafts`: (conversation_id, member_id, unique)

### Integration Domain
- `integrations`: (organization_id, provider)
- `events`: 
  - (organization_id, created_at DESC)
  - (aggregate_id, aggregate_type)
  - status
- `audit_logs`: 
  - (organization_id, created_at DESC)
  - resource_id
- `notifications`: 
  - (organization_id, recipient_id, created_at DESC)
  - status

## Seeding

Initial data is seeded by `app/db/seeders.py`.

### Seeded Data

**System Roles** (created per organization):
- `Admin`: Full access to all permissions
- `Manager`: Can manage members, conversations, teams
- `Agent`: Can handle conversations and send messages
- `Viewer`: Read-only access

Each role includes a specific set of permissions based on `PermissionEnum`.

## Development Workflow

```bash
# 1. Run migrations (one-time, creates collections + indexes)
python -m app.cli.db migrate

# 2. Seed data for your test organization
python -m app.cli.db seed "my-test-org-id"

# 3. Start development server
python -m uvicorn app.main:app --reload
```

## Production Deployment

```bash
# 1. Run migrations in production database
python -m app.cli.db migrate

# 2. Seed data for each customer organization
for org_id in $(list_org_ids); do
  python -m app.cli.db seed "$org_id"
done

# 3. Start API service
uvicorn app.main:app
```

## Troubleshooting

### Collections Not Created
- Verify MongoDB is running: `mongosh`
- Check connection string in `core/config.py`
- Run: `python -m app.cli.db migrate`

### Indexes Not Created
- Run: `python -m app.cli.db migrate`
- Verify indexes: `db.collection_name.getIndexes()`

### Seeding Issues
- Ensure organization exists before seeding
- Check org_id format (should be valid MongoDB ObjectId)
- Run: `python -m app.cli.db seed "<org_id>"`

## Index Performance Notes

### Hot Paths (Most Frequently Queried)
1. **Messages by Conversation** (DESC by created_at) - for pagination
2. **Conversations by Organization + Status** - for list views
3. **Conversations by Assigned Member** - for agent dashboards
4. **Customer Identities by Provider ID** - for webhook lookups

### Compound Index Strategy
- (organization_id, ...) first on most queries (multi-tenant filtering)
- (created_at, DESC) for chronological queries (message/event history)
- (provider, external_id) for provider lookups (webhook webhooks)

## MongoDB Atlas (Cloud)

If using MongoDB Atlas, indexes are created automatically during migration.

No additional setup required beyond providing `MONGODB_URL` in `.env`.

## Local Development with Docker

```bash
# Start MongoDB in Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Run migrations
python -m app.cli.db migrate

# Seed test data
python -m app.cli.db seed "test-org-123"
```

## Backup & Restore

```bash
# Backup database
mongodump --uri="mongodb://localhost:27017/boltchats" --out=./backup

# Restore database
mongorestore --uri="mongodb://localhost:27017" ./backup
```
