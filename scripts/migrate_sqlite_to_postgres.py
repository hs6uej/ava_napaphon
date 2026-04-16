#!/usr/bin/env python3
"""
Migrate call_history.db (SQLite) -> PostgreSQL.

Reads all rows from the SQLite tables (call_records, outbound_campaigns,
outbound_leads, outbound_attempts) and inserts them into the matching
PostgreSQL tables.  Existing rows (by primary key) are skipped via
ON CONFLICT DO NOTHING.

Usage:
    python scripts/migrate_sqlite_to_postgres.py

Requires:
    - psycopg2  (pip install psycopg2-binary)
    - python-dotenv
    - DATABASE_URL set in .env
    - SQLite file at data/call_history.db (configurable via CALL_HISTORY_DB_PATH)
"""

import os
import sys
import sqlite3
from pathlib import Path

# -- project root on sys.path -------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# -- load .env -----------------------------------------------------------------
load_dotenv(ROOT / ".env")

# -- import the canonical Postgres schema --------------------------------------
from core.db_schema_postgres import POSTGRES_SCHEMA_SQL


# ==============================================================================
#  Column maps (SQLite name -> list of column names, in INSERT order)
# ==============================================================================

TABLES = {
    "call_records": [
        "id", "call_id", "caller_number", "caller_name",
        "start_time", "end_time", "duration_seconds",
        "provider_name", "pipeline_name", "pipeline_components",
        "context_name", "conversation_history", "outcome",
        "transfer_destination", "error_message", "tool_calls",
        "avg_turn_latency_ms", "max_turn_latency_ms", "total_turns",
        "caller_audio_format", "codec_alignment_ok", "barge_in_count",
        "created_at",
    ],
    "outbound_campaigns": [
        "id", "name", "status", "timezone",
        "run_start_at_utc", "run_end_at_utc",
        "daily_window_start_local", "daily_window_end_local",
        "max_concurrent", "min_interval_seconds_between_calls",
        "default_context",
        "voicemail_drop_enabled", "voicemail_drop_mode",
        "voicemail_drop_text", "voicemail_drop_media_uri",
        "consent_enabled", "consent_media_uri", "consent_timeout_seconds",
        "amd_options_json",
        "created_at_utc", "updated_at_utc",
    ],
    "outbound_leads": [
        "id", "campaign_id", "name", "phone_number", "lead_timezone",
        "context_override", "caller_id_override", "custom_vars_json",
        "state", "attempt_count", "last_outcome",
        "last_attempt_at_utc", "leased_until_utc",
        "created_at_utc", "updated_at_utc",
    ],
    "outbound_attempts": [
        "id", "campaign_id", "lead_id",
        "started_at_utc", "ended_at_utc", "duration_seconds",
        "ari_channel_id", "outcome",
        "amd_status", "amd_cause",
        "consent_dtmf", "consent_result",
        "context", "provider", "call_history_call_id", "error_message",
    ],
}


# ==============================================================================
#  Helpers
# ==============================================================================

def pg_connect():
    """Open a psycopg2 connection from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not found in .env")
        sys.exit(1)

    parsed = urlparse(db_url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") or "postgres",
        user=parsed.username,
        password=parsed.password,
    )


def ensure_schema(pg_cur):
    """Run the canonical CREATE TABLE statements (idempotent)."""
    stmts = [s.strip() for s in POSTGRES_SCHEMA_SQL.split(";") if s.strip()]
    for stmt in stmts:
        pg_cur.execute(stmt)


def migrate_table(sqlite_cur, pg_cur, table, columns):
    """Copy every row from SQLite *table* into the Postgres table of the same name."""
    col_csv = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))

    # Read from SQLite
    sqlite_cur.execute("SELECT {} FROM {}".format(col_csv, table))
    rows = sqlite_cur.fetchall()

    if not rows:
        print("  SKIP  {}: 0 rows".format(table))
        return 0

    insert_sql = (
        "INSERT INTO {} ({}) VALUES ({}) "
        "ON CONFLICT (id) DO NOTHING"
    ).format(table, col_csv, placeholders)

    pg_cur.executemany(insert_sql, rows)
    print("  OK    {}: {} rows sent (duplicates skipped)".format(table, len(rows)))
    return len(rows)


# ==============================================================================
#  Main
# ==============================================================================

def main():
    # -- SQLite -----------------------------------------------------------------
    sqlite_path = ROOT / os.getenv("CALL_HISTORY_DB_PATH", "data/call_history.db")
    if not sqlite_path.exists():
        print("ERROR: SQLite file not found: {}".format(sqlite_path))
        sys.exit(1)

    db_url = os.getenv("DATABASE_URL", "")
    print("SQLite source : {}".format(sqlite_path))
    print("Postgres target: {}".format(db_url))
    print()

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_cur = sqlite_conn.cursor()

    # -- Postgres ---------------------------------------------------------------
    pg_conn = pg_connect()
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()

    try:
        # Ensure tables exist
        print("Ensuring PostgreSQL schema...")
        ensure_schema(pg_cur)
        print()

        # Migrate each table
        total = 0
        print("Migrating data...")
        for table, columns in TABLES.items():
            total += migrate_table(sqlite_cur, pg_cur, table, columns)

        pg_conn.commit()
        print("\nMigration complete - {} rows inserted.".format(total))

    except Exception as exc:
        pg_conn.rollback()
        print("\nMigration failed: {}".format(exc))
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        sqlite_cur.close()
        sqlite_conn.close()


if __name__ == "__main__":
    main()
