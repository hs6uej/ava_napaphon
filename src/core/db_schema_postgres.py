"""
PostgreSQL schema initialization script.

Creates all tables and indexes for the AVA AI Voice Agent application.
"""

POSTGRES_SCHEMA_SQL = """
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


def get_postgres_schema_statements():
    """
    Get PostgreSQL schema as a list of individual statements.
    
    Returns:
        List of SQL statements
    """
    # Split by semicolons, filter empty statements
    statements = [s.strip() for s in POSTGRES_SCHEMA_SQL.split(';') if s.strip()]
    return statements
