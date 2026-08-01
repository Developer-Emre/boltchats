# Production-Ready Database Module

Complete database management system with migration versioning, seeding, health checks, and validation.

## Architecture

```
database/
├── __init__.py              # Module entry point
├── migrations/
│   ├── __init__.py          # MigrationManager with versioning
│   ├── 001_create_collections.py
│   ├── 002_create_indexes.py
│   ├── 003_add_ttl_indexes.py
│   └── 004_add_missing_indexes.py
├── seeders/
│   └── __init__.py          # SeedManager with role templates
├── validators/
│   └── __init__.py          # DatabaseValidator
├── health/
│   └── __init__.py          # DatabaseHealth monitoring
├── backup/
│   └── __init__.py          # Backup/restore utilities
└── README.md                # This file
```

## Features

### 1. **Versioned Migrations**
- Numbered migration files (001_*, 002_*, etc.)
- Migration history tracking in MongoDB
- Automatic dependency management
- Rollback support

```python
# Run pending migrations
python -m app.cli.db migrate

# Rollback 2 versions
python -m app.cli.db rollback --steps 2

# Check status
python -m app.cli.db status
```

### 2. **Migration History**
- Tracks every applied migration
- Collection: `migration_history`
- Fields: `version`, `name`, `applied_at`, `status`
- Prevents duplicate runs

### 3. **Seeding with Templates**
- Template roles: Admin, Manager, Agent, Viewer
- Permission templates built-in
- Organization-specific seeding
- Reseed capability (delete + recreate)

```python
# Seed organization
python -m app.cli.db seed org_01K3F7M5Q9H6X

# Reseed (clean slate)
python -m app.cli.db reseed org_01K3F7M5Q9H6X
```

### 4. **TTL Indexes** (Automatic Cleanup)
- Drafts: 7 days
- Notifications: 30 days
- Event retries: 1 day
- No manual cleanup needed

### 5. **Critical Indexes**
- Query optimization for dashboard
- Soft delete support (deleted_at + conversation_id)
- Event replay optimization (aggregate_id + sequence)
- Unread badge queries (recipient_id + read)

### 6. **ULID IDs** (Time-sortable, Portable)
```python
from app.utils.ulid import new_organization_id, new_conversation_id

org_id = new_organization_id()  # org_01K3F7M5Q9H6X
conv_id = new_conversation_id()  # conv_01K3F7M5Q9H6X
```

Benefits:
- Time-sortable (unlike UUID)
- Distributed-safe (like UUID)
- Portable (works with PostgreSQL, etc.)
- Human-readable

### 7. **Health Checks**
Monitors:
- MongoDB connection
- Collections existence
- Index status
- Migration consistency
- TTL configuration

```python
python -m app.cli.db health
```

### 8. **Validation & Repair**
Validates:
- Organization references
- Member references
- Conversation references
- Message references (reply_to)

```python
python -m app.cli.db validate  # Check integrity
python -m app.cli.db repair    # Attempt repairs
```

## CLI Commands

```bash
# Migrations
python -m app.cli.db migrate [--version N]     # Run pending migrations
python -m app.cli.db rollback [--steps N]      # Rollback migrations
python -m app.cli.db status                    # Show migration status
python -m app.cli.db verify                    # Verify consistency

# Seeding
python -m app.cli.db seed <org_id>             # Seed organization
python -m app.cli.db reseed <org_id>           # Reseed organization

# Monitoring
python -m app.cli.db health                    # Health check
python -m app.cli.db validate                  # Validate integrity
python -m app.cli.db repair                    # Repair issues
```

## Environment-Specific Behavior

### Development
- Auto-migrate on startup (via management command)
- Permissive validation
- Full error details

### Production
- **Never** auto-migrate
- Require explicit `python -m app.cli.db migrate`
- Strict validation
- Error reporting to monitoring

## Migration Workflow

### Adding a New Migration

1. Create `00X_descriptive_name.py`
```python
from app.database.migrations import Migration

class MyMigration(Migration):
    version = 5
    name = "add_feature"
    description = "Add new feature to database"

    async def up(self, db):
        # Implementation
        pass

    async def down(self, db):
        # Rollback
        pass
```

2. Run migration
```bash
python -m app.cli.db migrate --version 5
```

3. Verify
```bash
python -m app.cli.db status
```

## Migration History Collection

```json
{
  "_id": "ObjectId",
  "version": 1,
  "name": "create_collections",
  "description": "Create all collections",
  "applied_at": "2024-08-01T12:00:00Z",
  "status": "applied"
}
```

## Indexes Strategy

### Fast Queries (Query Optimization)
- `organization_id + updated_at DESC` - Dashboard
- `recipient_id + read + created_at` - Unread badge
- `conversation_id + deleted_at + created_at` - Soft deletes

### Event Sourcing (Replay)
- `aggregate_id + sequence` - Fast replay
- `organization_id + aggregate_type + created_at` - Type filtering

### Referential Integrity
- `member_id + conversation_id` - Participant lookup
- `sender_id + created_at` - User history

## Backup & Restore

### Local Development (mongodump/mongorestore)
```python
from app.database.backup import BackupManager

manager = BackupManager("backups/")

# Backup
result = await manager.backup_database(
    mongo_uri="mongodb://localhost:27017",
    database_name="boltchats",
    tags=["daily", "prod"]
)

# List backups
backups = manager.list_backups()

# Restore
result = await manager.restore_database(
    mongo_uri="mongodb://localhost:27017",
    backup_path="backups/boltchats_20240801_120000",
    drop=False
)
```

### Production (Atlas Backup)
- Use MongoDB Atlas Backup service
- Automated daily backups
- Point-in-time recovery
- Geo-redundant storage

## Best Practices

### 1. Migration Naming
```
001_create_collections.py
002_create_indexes.py
003_add_ttl_indexes.py
004_add_missing_indexes.py
005_add_conversation_stats.py
```

### 2. Idempotent Migrations
```python
# ✅ Good - idempotent
async def up(self, db):
    try:
        await db.create_collection("my_collection")
    except Exception:
        pass  # Collection exists
```

### 3. Reversible Down Methods
```python
# ✅ Good - can be reversed
async def down(self, db):
    await db.drop_collection("my_collection")
```

### 4. Production Safety
```python
# Production config prevents auto-migration
if settings.environment == "production":
    # Migration only via CLI
    # Never auto-run
    pass
```

### 5. Regular Backups
```python
# Nightly backup job
python -m app.cli.db backup \
    --mongo-uri $MONGODB_URI \
    --database boltchats \
    --tags daily $(date +%Y-%m-%d)
```

## Troubleshooting

### Migration Stuck
```bash
# Check status
python -m app.cli.db status

# Verify consistency
python -m app.cli.db verify

# Manually rollback if needed
python -m app.cli.db rollback --steps 1
```

### Orphaned Documents
```bash
# Validate references
python -m app.cli.db validate

# Repair issues
python -m app.cli.db repair
```

### Index Problems
```bash
# Health check
python -m app.cli.db health

# Recreate if needed
python -m app.cli.db rollback --steps 1
python -m app.cli.db migrate --version 2
```

## Performance Considerations

### Index Sizes
Monitor index sizes:
```javascript
db.getCollection("messages").stats().indexSizes
```

### Compound Indexes
Prefer compound indexes for common queries:
```
organization_id (1) + updated_at (-1)  // Better than separate indexes
```

### TTL Overhead
TTL indexes add ~1% CPU overhead. Worth it for automatic cleanup.

## Monitoring

Health endpoint includes database status:
```bash
curl http://localhost:8000/health
# {
#   "status": "ok",
#   "service": "boltchats-api",
#   "database": "ok"
# }
```

## Further Reading

- [Migration Management](./migrations/README.md)
- [Index Strategy](./README.md#indexes-strategy)
- [Backup Strategy](./backup/__init__.py)
- [ULID Documentation](https://github.com/ahawker/ulid)
- [MongoDB TTL Indexes](https://docs.mongodb.com/manual/core/index-ttl/)
