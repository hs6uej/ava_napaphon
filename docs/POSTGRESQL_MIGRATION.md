# PostgreSQL Migration Guide

This guide explains how to migrate from SQLite to PostgreSQL for the AVA AI Voice Agent application.

## Overview

The application now supports both SQLite and PostgreSQL databases. The database is selected based on the `DATABASE_URL` environment variable:

- **No DATABASE_URL set**: Uses SQLite (default, backward compatible)
- **DATABASE_URL set**: Uses PostgreSQL

## Prerequisites

1. PostgreSQL server running (e.g., localhost:32857)
2. Database created for the application
3. Python 3.8+ with required packages

## Step 1: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 2: Set Up PostgreSQL Database

### Option A: Using existing PostgreSQL on localhost:32857

```bash
# Connect to PostgreSQL
psql -h localhost -p 32857 -U postgres

# Create database
CREATE DATABASE ava_db;

# Create user (optional)
CREATE USER ava_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE ava_db TO ava_user;
```

### Option B: Using Docker

```bash
# Run PostgreSQL in Docker
docker run -d \
  --name ava-postgres \
  -p 32857:5432 \
  -e POSTGRES_DB=ava_db \
  -e POSTGRES_USER=ava_user \
  -e POSTGRES_PASSWORD=your_secure_password \
  postgres:15-alpine

# Wait for PostgreSQL to start
sleep 5
```

## Step 3: Configure Environment Variables

Set the `DATABASE_URL` environment variable to point to your PostgreSQL database:

```bash
# Format: postgresql://user:password@host:port/database
export DATABASE_URL="postgresql://ava_user:your_secure_password@localhost:32857/ava_db"

# Or add to your .env file
echo "DATABASE_URL=postgresql://ava_user:your_secure_password@localhost:32857/ava_db" >> .env
```

**Important**: Keep your existing `CALL_HISTORY_DB_PATH` for SQLite fallback if needed:

```bash
export CALL_HISTORY_DB_PATH="data/call_history.db"
```

## Step 4: Initialize PostgreSQL Schema

Run the schema initialization script to create all tables and indexes:

```bash
# Ensure DATABASE_URL is set
export DATABASE_URL="postgresql://ava_user:your_secure_password@localhost:32857/ava_db"

# Run schema initialization
python scripts/init_postgres_schema.py
```

Expected output:
```
INFO - Initializing PostgreSQL schema...
INFO - Connecting to PostgreSQL at localhost:32857
INFO - Executing 18 SQL statements...
INFO - ✓ PostgreSQL schema initialized successfully
INFO - ✓ Created 4 tables: call_records, outbound_attempts, outbound_campaigns, outbound_leads
```

## Step 5: Migrate Data from SQLite (Optional)

If you have existing data in SQLite, migrate it to PostgreSQL:

```bash
# Set both environment variables
export CALL_HISTORY_DB_PATH="data/call_history.db"  # Your SQLite database
export DATABASE_URL="postgresql://ava_user:your_secure_password@localhost:32857/ava_db"

# Run migration
python scripts/migrate_sqlite_to_postgres.py
```

Expected output:
```
============================================================
Starting database migration: SQLite → PostgreSQL
============================================================
INFO - Connecting to SQLite: data/call_history.db
INFO - SQLite connection established
INFO - Connecting to PostgreSQL
INFO - PostgreSQL connection established
INFO - Creating PostgreSQL schema...
INFO - PostgreSQL schema created successfully
INFO - Migrating table call_records (150 rows)...
INFO -   Migrated 100/150 rows...
INFO - ✓ Successfully migrated 150 rows from call_records
INFO - Migrating table outbound_campaigns (3 rows)...
INFO - ✓ Successfully migrated 3 rows from outbound_campaigns
INFO - Migrating table outbound_leads (250 rows)...
INFO - ✓ Successfully migrated 250 rows from outbound_leads

Verifying migration...
✓ call_records: SQLite=150, PostgreSQL=150
✓ outbound_campaigns: SQLite=3, PostgreSQL=3
✓ outbound_leads: SQLite=250, PostgreSQL=250

✓ Migration completed successfully!
============================================================
```

## Step 6: Start the Application

The application will automatically detect and use PostgreSQL:

```bash
# Make sure DATABASE_URL is set
export DATABASE_URL="postgresql://ava_user:your_secure_password@localhost:32857/ava_db"

# Start the application
python main.py
```

You should see log entries confirming PostgreSQL connection:
```
INFO - Connecting to PostgreSQL database
```

## Verification

### Check Tables Were Created

```bash
psql -h localhost -p 32857 -U ava_user -d ava_db -c "\dt"
```

Expected output:
```
                List of relations
 Schema |         Name          | Type  |   Owner   
--------+-----------------------+-------+-----------
 public | call_records          | table | ava_user
 public | outbound_attempts     | table | ava_user
 public | outbound_campaigns    | table | ava_user
 public | outbound_leads        | table | ava_user
```

### Check Row Counts

```bash
psql -h localhost -p 32857 -U ava_user -d ava_db <<EOF
SELECT 'call_records' as table_name, COUNT(*) as rows FROM call_records
UNION ALL
SELECT 'outbound_campaigns', COUNT(*) FROM outbound_campaigns
UNION ALL
SELECT 'outbound_leads', COUNT(*) FROM outbound_leads
UNION ALL
SELECT 'outbound_attempts', COUNT(*) FROM outbound_attempts;
EOF
```

## Database Schema

### Tables Created

1. **call_records**: Historical call data and analytics
   - Primary key: `id` (TEXT/UUID)
   - Indexed: `start_time`, `caller_number`, `outcome`, `provider_name`, `pipeline_name`, `context_name`

2. **outbound_campaigns**: Outbound dialing campaigns
   - Primary key: `id` (TEXT/UUID)
   - Indexed: `status`

3. **outbound_leads**: Campaign leads/phone numbers
   - Primary key: `id` (TEXT/UUID)
   - Unique constraint: `(campaign_id, phone_number)`
   - Indexed: `(campaign_id, state)`, `(campaign_id, phone_number)`

4. **outbound_attempts**: Call attempt history
   - Primary key: `id` (TEXT/UUID)
   - Indexed: `(campaign_id, started_at_utc)`, `(lead_id, started_at_utc)`

## Environment Variable Reference

```bash
# PostgreSQL connection (required for PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# SQLite fallback path (optional, for backward compatibility)
CALL_HISTORY_DB_PATH=data/call_history.db

# Call history settings
CALL_HISTORY_ENABLED=true
CALL_HISTORY_RETENTION_DAYS=0  # 0 = keep forever
```

## Switching Back to SQLite

To revert to SQLite, simply unset the `DATABASE_URL` environment variable:

```bash
unset DATABASE_URL
```

The application will automatically fall back to SQLite using `CALL_HISTORY_DB_PATH`.

## Troubleshooting

### Connection Refused

```
ERROR: Failed to connect to PostgreSQL: connection refused
```

**Solution**: Ensure PostgreSQL is running and accessible:
```bash
# Check if PostgreSQL is listening
netstat -an | grep 32857

# Or test connection
pg_isready -h localhost -p 32857
```

### Authentication Failed

```
ERROR: Failed to connect to PostgreSQL: authentication failed
```

**Solution**: Verify username, password, and database name in DATABASE_URL.

### Schema Already Exists

If tables already exist, the schema initialization is idempotent (uses `CREATE TABLE IF NOT EXISTS`). It's safe to run multiple times.

### Migration Verification Failed

If row counts don't match after migration:

1. Check the migration log for errors
2. Verify SQLite database path is correct
3. Ensure PostgreSQL schema was created successfully
4. Try running migration again (it will clear and re-import)

## Performance Notes

### PostgreSQL Advantages

- Better concurrent read/write performance
- Native JSON support for complex fields
- Superior indexing and query optimization
- Connection pooling support
- Replication and high availability

### SQLite Advantages

- Zero configuration
- Embedded (no separate server)
- Perfect for development and small deployments
- Portable database file

## Production Deployment

For production, we recommend:

1. Use PostgreSQL with proper backup strategy
2. Set up connection pooling (e.g., PgBouncer)
3. Configure PostgreSQL for your workload:
   ```sql
   ALTER SYSTEM SET max_connections = 100;
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   SELECT pg_reload_conf();
   ```
4. Enable SSL/TLS for encrypted connections
5. Set up monitoring (pg_stat_statements, logging)

## Support

For issues or questions:
- Check application logs for detailed error messages
- Verify all environment variables are set correctly
- Test database connectivity independently with `psql` or `pg_isready`
- Review the [PostgreSQL documentation](https://www.postgresql.org/docs/)

---

**Migration completed successfully!** Your application is now running on PostgreSQL.
