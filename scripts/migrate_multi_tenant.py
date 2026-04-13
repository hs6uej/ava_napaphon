#!/usr/bin/env python3
"""
Multi-tenancy Database Migration Script for AAVA.

This script adds support for hosting multiple customers (tenants) on a single 
AVA instance by adding tenant_id columns and relevant management tables.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.db_connection import get_db_connection, is_postgres, adapt_sql_for_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MIGRATION_SQL = """
-- 1. Create Tenants Table
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    account_status TEXT DEFAULT 'active', -- active, suspended, trial
    api_key TEXT UNIQUE,
    azure_oid TEXT UNIQUE, -- Azure Object ID for user-level mapping
    azure_tid TEXT,        -- Azure Tenant ID for tenant-level mapping
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create Tenant Settings (Dynamic Config)
CREATE TABLE IF NOT EXISTS tenant_settings (
    tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    greeting_message TEXT,
    system_prompt TEXT,
    transfer_number TEXT,
    working_hours_json TEXT DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Create DID Mapping (Phone Number -> Tenant)
CREATE TABLE IF NOT EXISTS tenant_dids (
    phone_number TEXT PRIMARY KEY, -- DID (e.g. +66812345678)
    tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    context_name TEXT DEFAULT 'default',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Update existing tables to include tenant_id
-- We use a try-except logic in Python to add columns if they don't exist
"""

def add_column_if_not_exists(conn, table, column, col_type):
    """Safely add a column to a table if it doesn't already exist."""
    try:
        cursor = conn.cursor()
        if is_postgres():
            # Check if column exists in Postgres
            cursor.execute(f"""
                SELECT count(*) FROM information_schema.columns 
                WHERE table_name='{table}' AND column_name='{column}';
            """)
            res = cursor.fetchone()
            count = res[0] if isinstance(res, (list, tuple)) else list(res.values())[0]
            if count == 0:
                logger.info(f"Adding column '{column}' to table '{table}' (Postgres)...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")
        else:
            # Check if column exists in SQLite
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [info[1] for info in cursor.fetchall()]
            if column not in columns:
                logger.info(f"Adding column '{column}' to table '{table}' (SQLite)...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to add column {column} to {table}: {e}")
        conn.rollback()

def run_migration():
    """Main migration entry point."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logger.info("Starting multi-tenancy migration...")

        # 1. Create new management tables
        for statement in [s.strip() for s in MIGRATION_SQL.split(';') if s.strip()]:
            adapted = adapt_sql_for_db(statement)
            try:
                cursor.execute(adapted)
            except Exception as e:
                # If table already exists or references fail, log and continue
                logger.debug(f"Statement failed (possibly already exists): {e}")
        
        conn.commit()
        logger.info("Base management tables created.")

        # 2. Add tenant_id to active tracking tables
        tables_to_update = [
            ('call_records', 'TEXT'),
            ('outbound_campaigns', 'TEXT'),
            ('outbound_leads', 'TEXT'),
            ('outbound_attempts', 'TEXT')
        ]

        for table, col_type in tables_to_update:
            add_column_if_not_exists(conn, table, 'tenant_id', col_type)

        # Add Azure columns specifically to tenants table if it was created before this update
        add_column_if_not_exists(conn, 'tenants', 'azure_oid', 'TEXT')
        add_column_if_not_exists(conn, 'tenants', 'azure_tid', 'TEXT')

        logger.info("Migrated existing tables to include tenant_id.")

        # 3. Create a default 'Master' tenant if none exists
        cursor.execute("SELECT COUNT(*) FROM tenants;")
        res = cursor.fetchone()
        tenant_count = res[0] if isinstance(res, (list, tuple)) else list(res.values())[0]
        if tenant_count == 0:
            import uuid
            master_id = str(uuid.uuid4())
            logger.info(f"Creating default Master tenant with ID {master_id}...")
            cursor.execute(
                "INSERT INTO tenants (id, name, account_status) VALUES (?, ?, ?);".replace('?', '%s') if is_postgres() else "INSERT INTO tenants (id, name, account_status) VALUES (?, ?, ?);",
                (master_id, "Master Account", "active")
            )
            # Default settings
            cursor.execute(
                "INSERT INTO tenant_settings (tenant_id, greeting_message, system_prompt) VALUES (?, ?, ?);".replace('?', '%s') if is_postgres() else "INSERT INTO tenant_settings (tenant_id, greeting_message, system_prompt) VALUES (?, ?, ?);",
                (master_id, os.getenv("GREETING", "Hello"), os.getenv("AI_ROLE", "Helpful assistant"))
            )
            conn.commit()

        logger.info("✅ Multi-tenancy migration complete!")

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migration()
