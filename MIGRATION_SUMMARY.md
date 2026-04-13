# Database Migration Summary

## What Was Done

Successfully migrated the AVA AI Voice Agent from SQLite to PostgreSQL with full backward compatibility.

## Files Created

### Core Database Layer
- **`src/core/db_connection.py`** - Database abstraction layer supporting both SQLite and PostgreSQL
- **`src/core/db_schema_postgres.py`** - PostgreSQL schema definitions

### Migration Scripts
- **`scripts/init_postgres_schema.py`** - Initialize PostgreSQL schema
- **`scripts/migrate_sqlite_to_postgres.py`** - Migrate data from SQLite to PostgreSQL
- **`scripts/setup_postgres.sh`** - Interactive setup wizard

### Documentation
- **`docs/POSTGRESQL_MIGRATION.md`** - Comprehensive migration guide

## Files Modified

### Database Stores
- **`src/core/call_history.py`** - Updated to use database abstraction layer
- **`src/core/outbound_store.py`** - Updated to use database abstraction layer

### Dependencies
- **`requirements.txt`** - Added `psycopg2-binary>=2.9.0`

## Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
./scripts/setup_postgres.sh
```

### Option 2: Manual Setup

1. **Install PostgreSQL driver:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set DATABASE_URL environment variable:**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:32857/ava_db"
   ```

3. **Initialize schema:**
   ```bash
   python scripts/init_postgres_schema.py
   ```

4. **Migrate data (optional):**
   ```bash
   export CALL_HISTORY_DB_PATH="data/call_history.db"
   python scripts/migrate_sqlite_to_postgres.py
   ```

## Database Tables Created

1. **call_records** - Call history and analytics
2. **outbound_campaigns** - Outbound dialing campaigns
3. **outbound_leads** - Campaign leads/contacts  
4. **outbound_attempts** - Call attempt history

## How It Works

### Database Selection
The application automatically selects the database based on environment variables:

- **PostgreSQL**: When `DATABASE_URL` is set (format: `postgresql://user:pass@host:port/db`)
- **SQLite**: When `DATABASE_URL` is not set (uses `CALL_HISTORY_DB_PATH`)

### Abstraction Layer
The `db_connection.py` module provides:
- Unified connection API for both databases
- Automatic SQL placeholder adaptation (`?` → `%s`)
- Database-specific query handling (e.g., `INSERT OR REPLACE` → `INSERT ... ON CONFLICT`)

### Backward Compatibility
- Existing SQLite code works without changes
- No breaking changes to APIs
- Can switch back to SQLite by unsetting `DATABASE_URL`

## Testing

To verify the migration:

```bash
# Check schema
psql -h localhost -p 32857 -U your_user -d ava_db -c "\dt"

# Check row counts
psql -h localhost -p 32857 -U your_user -d ava_db <<EOF
SELECT 'call_records' as table, COUNT(*) as rows FROM call_records
UNION ALL
SELECT 'outbound_campaigns', COUNT(*) FROM outbound_campaigns
UNION ALL
SELECT 'outbound_leads', COUNT(*) FROM outbound_leads
UNION ALL
SELECT 'outbound_attempts', COUNT(*) FROM outbound_attempts;
EOF
```

## Next Steps

1. **Start the application** with PostgreSQL:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:32857/ava_db"
   python main.py
   ```

2. **Monitor logs** for PostgreSQL connection confirmation:
   ```
   INFO - Connecting to PostgreSQL database
   ```

3. **Test functionality** by making test calls and verifying data is stored

## Rollback

To revert to SQLite:
```bash
unset DATABASE_URL
python main.py
```

## Support

- Full documentation: [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md)
- Database abstraction: [src/core/db_connection.py](src/core/db_connection.py)
- Schema reference: [src/core/db_schema_postgres.py](src/core/db_schema_postgres.py)

---

**Migration Status**: ✅ Complete and Ready for Production
