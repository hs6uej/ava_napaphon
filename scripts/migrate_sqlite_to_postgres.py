#!/usr/bin/env python3
"""
Database migration script: SQLite to PostgreSQL

This script migrates data from SQLite to PostgreSQL for the AVA AI Voice Agent.

Usage:
    python scripts/migrate_sqlite_to_postgres.py

Environment variables required:
    DATABASE_URL - PostgreSQL connection string (e.g., postgresql://user:pass@localhost:32857/ava_db)
    CALL_HISTORY_DB_PATH - Path to existing SQLite database (default: data/call_history.db)
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import sqlite3
import psycopg2
import psycopg2.extras
from urllib.parse import urlparse
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Migrate data from SQLite to PostgreSQL."""
    
    TABLES = [
        'call_records',
        'outbound_campaigns',
        'outbound_leads',
        'outbound_attempts'
    ]
    
    def __init__(self, sqlite_path: str, postgres_url: str):
        self.sqlite_path = sqlite_path
        self.postgres_url = postgres_url
        self.sqlite_conn = None
        self.postgres_conn = None
    
    def connect_sqlite(self):
        """Connect to SQLite database."""
        logger.info(f"Connecting to SQLite: {self.sqlite_path}")
        if not os.path.exists(self.sqlite_path):
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")
        
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row
        logger.info("SQLite connection established")
    
    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        logger.info(f"Connecting to PostgreSQL")
        
        parsed = urlparse(self.postgres_url)
        
        self.postgres_conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/') if parsed.path else 'postgres',
            user=parsed.username,
            password=parsed.password
        )
        self.postgres_conn.autocommit = False
        logger.info("PostgreSQL connection established")
    
    def create_postgres_schema(self):
        """Create PostgreSQL schema."""
        logger.info("Creating PostgreSQL schema...")
        
        # Schema SQL embedded directly to avoid import issues
        schema_sql = """
        -- Call History table
        CREATE TABLE IF NOT EXISTS call_records (
            id TEXT PRIMARY KEY,
            call_id TEXT NOT NULL,
            caller_number TEXT,
            caller_name TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration_seconds REAL,
            provider_name TEXT,
            pipeline_name TEXT,
            pipeline_components TEXT,
            context_name TEXT,
            conversation_history TEXT,
            outcome TEXT,
            transfer_destination TEXT,
            error_message TEXT,
            tool_calls TEXT,
            avg_turn_latency_ms REAL,
            max_turn_latency_ms REAL,
            total_turns INTEGER,
            caller_audio_format TEXT,
            codec_alignment_ok INTEGER,
            barge_in_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_call_records_start_time ON call_records(start_time);
        CREATE INDEX IF NOT EXISTS idx_call_records_caller_number ON call_records(caller_number);
        CREATE INDEX IF NOT EXISTS idx_call_records_outcome ON call_records(outcome);
        CREATE INDEX IF NOT EXISTS idx_call_records_provider ON call_records(provider_name);
        CREATE INDEX IF NOT EXISTS idx_call_records_pipeline ON call_records(pipeline_name);
        CREATE INDEX IF NOT EXISTS idx_call_records_context ON call_records(context_name);

        -- Outbound Campaigns table
        CREATE TABLE IF NOT EXISTS outbound_campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            timezone TEXT NOT NULL DEFAULT 'UTC',
            run_start_at_utc TIMESTAMP,
            run_end_at_utc TIMESTAMP,
            daily_window_start_local TEXT NOT NULL DEFAULT '09:00',
            daily_window_end_local TEXT NOT NULL DEFAULT '17:00',
            max_concurrent INTEGER NOT NULL DEFAULT 1,
            min_interval_seconds_between_calls INTEGER NOT NULL DEFAULT 5,
            default_context TEXT NOT NULL DEFAULT 'default',
            voicemail_drop_enabled INTEGER NOT NULL DEFAULT 1,
            voicemail_drop_mode TEXT NOT NULL DEFAULT 'upload',
            voicemail_drop_text TEXT,
            voicemail_drop_media_uri TEXT,
            consent_enabled INTEGER NOT NULL DEFAULT 0,
            consent_media_uri TEXT,
            consent_timeout_seconds INTEGER NOT NULL DEFAULT 5,
            amd_options_json TEXT NOT NULL DEFAULT '{}',
            created_at_utc TIMESTAMP NOT NULL,
            updated_at_utc TIMESTAMP NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_outbound_campaigns_status ON outbound_campaigns(status);

        -- Outbound Leads table
        CREATE TABLE IF NOT EXISTS outbound_leads (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            name TEXT,
            phone_number TEXT NOT NULL,
            lead_timezone TEXT,
            context_override TEXT,
            caller_id_override TEXT,
            custom_vars_json TEXT NOT NULL DEFAULT '{}',
            state TEXT NOT NULL DEFAULT 'pending',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            last_outcome TEXT,
            last_attempt_at_utc TIMESTAMP,
            leased_until_utc TIMESTAMP,
            created_at_utc TIMESTAMP NOT NULL,
            updated_at_utc TIMESTAMP NOT NULL,
            UNIQUE(campaign_id, phone_number)
        );

        CREATE INDEX IF NOT EXISTS idx_outbound_leads_campaign_state ON outbound_leads(campaign_id, state);
        CREATE INDEX IF NOT EXISTS idx_outbound_leads_campaign_phone ON outbound_leads(campaign_id, phone_number);

        -- Outbound Attempts table
        CREATE TABLE IF NOT EXISTS outbound_attempts (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            lead_id TEXT NOT NULL,
            started_at_utc TIMESTAMP NOT NULL,
            ended_at_utc TIMESTAMP,
            duration_seconds INTEGER,
            ari_channel_id TEXT,
            outcome TEXT,
            amd_status TEXT,
            amd_cause TEXT,
            consent_dtmf TEXT,
            consent_result TEXT,
            context TEXT,
            provider TEXT,
            call_history_call_id TEXT,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_outbound_attempts_campaign_started ON outbound_attempts(campaign_id, started_at_utc);
        CREATE INDEX IF NOT EXISTS idx_outbound_attempts_lead_started ON outbound_attempts(lead_id, started_at_utc);
        """
        
        cursor = self.postgres_conn.cursor()
        
        try:
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            
            self.postgres_conn.commit()
            logger.info("PostgreSQL schema created successfully")
        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"Failed to create schema: {e}")
            raise
        finally:
            cursor.close()
    
    def get_table_columns(self, table_name: str) -> list:
        """Get column names from SQLite table."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall()]
        cursor.close()
        return columns
    
    def table_exists_in_sqlite(self, table_name: str) -> bool:
        """Check if table exists in SQLite."""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
    
    def get_row_count(self, table_name: str, conn) -> int:
        """Get row count from table."""
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        row = cursor.fetchone()
        count = row['count'] if hasattr(row, 'keys') else row[0]
        cursor.close()
        return count
    
    def migrate_table(self, table_name: str):
        """Migrate a single table from SQLite to PostgreSQL."""
        
        if not self.table_exists_in_sqlite(table_name):
            logger.warning(f"Table {table_name} does not exist in SQLite, skipping...")
            return
        
        # Get row count
        row_count = self.get_row_count(table_name, self.sqlite_conn)
        
        if row_count == 0:
            logger.info(f"Table {table_name} is empty, skipping...")
            return
        
        logger.info(f"Migrating table {table_name} ({row_count} rows)...")
        
        # Get columns
        columns = self.get_table_columns(table_name)
        
        # Read all data from SQLite
        sqlite_cursor = self.sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        sqlite_cursor.close()
        
        # Insert into PostgreSQL
        postgres_cursor = self.postgres_conn.cursor()
        
        try:
            # Clear existing data in PostgreSQL table
            postgres_cursor.execute(f"DELETE FROM {table_name}")
            
            # Prepare insert statement
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert rows
            migrated = 0
            for row in rows:
                # Convert row to tuple
                values = tuple(row[col] for col in columns)
                postgres_cursor.execute(insert_sql, values)
                migrated += 1
                
                if migrated % 100 == 0:
                    logger.info(f"  Migrated {migrated}/{row_count} rows...")
            
            self.postgres_conn.commit()
            logger.info(f"✓ Successfully migrated {migrated} rows from {table_name}")
            
        except Exception as e:
            self.postgres_conn.rollback()
            logger.error(f"✗ Failed to migrate table {table_name}: {e}")
            raise
        finally:
            postgres_cursor.close()
    
    def verify_migration(self):
        """Verify that migration was successful."""
        logger.info("\nVerifying migration...")
        
        all_match = True
        
        for table_name in self.TABLES:
            if not self.table_exists_in_sqlite(table_name):
                continue
            
            sqlite_count = self.get_row_count(table_name, self.sqlite_conn)
            postgres_count = self.get_row_count(table_name, self.postgres_conn)
            
            match = sqlite_count == postgres_count
            symbol = "✓" if match else "✗"
            
            logger.info(
                f"{symbol} {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}"
            )
            
            if not match:
                all_match = False
        
        if all_match:
            logger.info("\n✓ Migration verification PASSED")
        else:
            logger.error("\n✗ Migration verification FAILED - row counts don't match")
        
        return all_match
    
    def run(self):
        """Run the complete migration."""
        try:
            logger.info("=" * 60)
            logger.info("Starting database migration: SQLite → PostgreSQL")
            logger.info("=" * 60)
            
            # Connect to databases
            self.connect_sqlite()
            self.connect_postgres()
            
            # Create schema
            self.create_postgres_schema()
            
            # Migrate tables
            for table_name in self.TABLES:
                self.migrate_table(table_name)
            
            # Verify migration
            success = self.verify_migration()
            
            logger.info("=" * 60)
            if success:
                logger.info("✓ Migration completed successfully!")
            else:
                logger.error("✗ Migration completed with warnings")
            logger.info("=" * 60)
            
            return success
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return False
        
        finally:
            if self.sqlite_conn:
                self.sqlite_conn.close()
            if self.postgres_conn:
                self.postgres_conn.close()


def main():
    """Main entry point."""
    
    # Get configuration from environment
    postgres_url = os.getenv('DATABASE_URL')
    sqlite_path = os.getenv('CALL_HISTORY_DB_PATH', 'data/call_history.db')
    
    if not postgres_url:
        logger.error("ERROR: DATABASE_URL environment variable not set")
        logger.error("Usage: DATABASE_URL=postgresql://user:pass@localhost:32857/ava_db python scripts/migrate_sqlite_to_postgres.py")
        sys.exit(1)
    
    if not postgres_url.startswith(('postgresql://', 'postgres://')):
        logger.error(f"ERROR: Invalid DATABASE_URL (must start with postgresql:// or postgres://): {postgres_url}")
        sys.exit(1)
    
    # Run migration
    migrator = DatabaseMigrator(sqlite_path, postgres_url)
    success = migrator.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
