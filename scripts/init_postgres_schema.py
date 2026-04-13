#!/usr/bin/env python3
"""
Initialize PostgreSQL database schema for AVA AI Voice Agent.

This script creates all necessary tables and indexes in PostgreSQL.

Usage:
    python scripts/init_postgres_schema.py

Environment variables required:
    DATABASE_URL - PostgreSQL connection string (e.g., postgresql://user:pass@localhost:32857/ava_db)
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import psycopg2
from urllib.parse import urlparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_schema(postgres_url: str):
    """Initialize PostgreSQL schema."""
    
    logger.info("Initializing PostgreSQL schema...")
    
    # Parse URL
    parsed = urlparse(postgres_url)
    
    # Connect to PostgreSQL
    logger.info(f"Connecting to PostgreSQL at {parsed.hostname}:{parsed.port or 5432}")
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/') if parsed.path else 'postgres',
        user=parsed.username,
        password=parsed.password
    )
    conn.autocommit = False
    
    try:
        cursor = conn.cursor()
        
        try:
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
            
            # Split by semicolons, filter empty statements
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            logger.info(f"Executing {len(statements)} SQL statements...")
            
            for i, statement in enumerate(statements, 1):
                if statement.strip():
                    logger.debug(f"Statement {i}: {statement[:50]}...")
                    cursor.execute(statement)
            
            conn.commit()
            logger.info("PostgreSQL schema initialized successfully")
            
            # Verify tables were created
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")
            
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create schema: {e}")
            raise
        finally:
            cursor.close()
            
    finally:
        conn.close()


def main():
    """Main entry point."""
    
    postgres_url = os.getenv('DATABASE_URL')
    
    if not postgres_url:
        logger.error("ERROR: DATABASE_URL environment variable not set")
        logger.error("Usage: DATABASE_URL=postgresql://user:pass@localhost:32857/ava_db python scripts/init_postgres_schema.py")
        sys.exit(1)
    
    if not postgres_url.startswith(('postgresql://', 'postgres://')):
        logger.error(f"ERROR: Invalid DATABASE_URL: {postgres_url}")
        sys.exit(1)
    
    try:
        init_schema(postgres_url)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Schema initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
