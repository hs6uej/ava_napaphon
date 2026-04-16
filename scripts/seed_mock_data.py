#!/usr/bin/env python3
"""
Seed PostgreSQL with mock data for AVA AI Voice Agent.
"""

import os
import sys
import uuid
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def get_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env")
        sys.exit(1)
        
    parsed = urlparse(db_url)
    return psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/') if parsed.path else 'postgres',
        user=parsed.username,
        password=parsed.password
    )

def seed_data():
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor()
    
    try:
        now = datetime.now(timezone.utc)
        
        # 1. Seed Outbound Campaigns
        print("Seeding outbound_campaigns...")
        campaign_ids = [str(uuid.uuid4()) for _ in range(2)]
        campaign_data = [
            (
                campaign_ids[0],
                "Sales Promotion April 2026",
                "running",
                "Asia/Bangkok",
                now - timedelta(days=1),
                now + timedelta(days=7),
                "09:00",
                "18:00",
                3,
                10,
                "sales_context",
                1, "upload", None, "media/promotions/promo_v1.wav",
                0, None, 5,
                json.dumps({"silence_threshold": 256, "answer_timeout_ms": 5000}),
                now - timedelta(days=2),
                now - timedelta(hours=5)
            ),
            (
                campaign_ids[1],
                "Customer Feedback Survey",
                "draft",
                "Asia/Bangkok",
                None, None,
                "10:00",
                "17:00",
                1,
                30,
                "survey_context",
                0, "tts", "Please take a moment to rate our service.", None,
                1, "media/consent/survey_consent.wav", 10,
                json.dumps({}),
                now - timedelta(days=1),
                now - timedelta(days=1)
            )
        ]
        
        cur.executemany("""
            INSERT INTO outbound_campaigns (
                id, name, status, timezone, run_start_at_utc, run_end_at_utc,
                daily_window_start_local, daily_window_end_local,
                max_concurrent, min_interval_seconds_between_calls,
                default_context, voicemail_drop_enabled, voicemail_drop_mode,
                voicemail_drop_text, voicemail_drop_media_uri,
                consent_enabled, consent_media_uri, consent_timeout_seconds,
                amd_options_json, created_at_utc, updated_at_utc
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, campaign_data)
        
        # 2. Seed Outbound Leads
        print("Seeding outbound_leads...")
        lead_ids = []
        lead_data = []
        first_names = ["Somsak", "Wichai", "Anucha", "Malee", "Suda", "Kanya", "Prasert", "Naree"]
        last_names = ["Saetang", "Rattanaporn", "Boonmee", "Srisuwan", "Chaisri", "Klaewkla"]
        
        for i in range(30):
            l_id = str(uuid.uuid4())
            lead_ids.append(l_id)
            c_id = campaign_ids[i % 2]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            phone = f"08{random.randint(10000000, 99999999)}"
            state = random.choice(["pending", "completed", "failed"]) if i < 20 else "pending"
            
            lead_data.append((
                l_id, c_id, name, phone, "Asia/Bangkok", None, None,
                json.dumps({"customer_segment": "gold" if i % 5 == 0 else "regular"}),
                state, random.randint(0, 3),
                "human" if state == "completed" else ("no-answer" if state == "failed" else None),
                now - timedelta(hours=random.randint(1, 48)) if state != "pending" else None,
                None,
                now - timedelta(days=5),
                now - timedelta(hours=random.randint(1, 10))
            ))
            
        cur.executemany("""
            INSERT INTO outbound_leads (
                id, campaign_id, name, phone_number, lead_timezone,
                context_override, caller_id_override, custom_vars_json,
                state, attempt_count, last_outcome, last_attempt_at_utc,
                leased_until_utc, created_at_utc, updated_at_utc
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, lead_data)
        
        # 3. Seed Outbound Attempts
        print("Seeding outbound_attempts...")
        attempt_data = []
        for i in range(10):
            a_id = str(uuid.uuid4())
            l_idx = random.randint(0, 29)
            l_id = lead_ids[l_idx]
            c_id = lead_data[l_idx][1]
            start = now - timedelta(hours=random.randint(1, 24))
            duration = random.randint(10, 120)
            
            attempt_data.append((
                a_id, c_id, l_id, start, start + timedelta(seconds=duration),
                duration, f"channel-{random.randint(1000, 9999)}",
                "completed", "human", "ack", "1", "agreed",
                "sales_context", "openai", str(uuid.uuid4()), None
            ))
            
        cur.executemany("""
            INSERT INTO outbound_attempts (
                id, campaign_id, lead_id, started_at_utc, ended_at_utc,
                duration_seconds, ari_channel_id, outcome, amd_status,
                amd_cause, consent_dtmf, consent_result, context,
                provider, call_history_call_id, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, attempt_data)
        
        # 4. Seed Call Records
        print("Seeding call_records...")
        call_records = []
        outcomes = ["completed", "error", "abandoned", "transferred"]
        providers = ["openai", "google", "deepgram"]
        
        for i in range(15):
            call_id = str(uuid.uuid4())
            start = now - timedelta(hours=random.randint(0, 48))
            duration = random.uniform(20.0, 300.0)
            end = start + timedelta(seconds=duration)
            
            call_records.append((
                str(uuid.uuid4()), call_id, 
                f"08{random.randint(10000000, 99999999)}",
                random.choice(first_names),
                start, end, duration,
                random.choice(providers), "default_pipeline",
                json.dumps({"stt": "whisper", "llm": "gpt-4", "tts": "elevenlabs"}),
                "customer_service",
                json.dumps([
                    {"role": "assistant", "content": "สวัสดีค่ะ มีอะไรให้ช่วยคะ?"},
                    {"role": "user", "content": "อยากสอบถามโปรโมชั่นค่ะ"}
                ]),
                random.choice(outcomes),
                "1001" if random.random() > 0.8 else None,
                "API key expired" if i == 0 else None,
                json.dumps([]),
                random.uniform(200, 800), random.uniform(1000, 1500),
                random.randint(2, 10), "ulaw", 1, 0,
                1 if i % 3 == 0 else 0,
                now
            ))
            
        cur.executemany("""
            INSERT INTO call_records (
                id, call_id, caller_number, caller_name,
                start_time, end_time, duration_seconds,
                provider_name, pipeline_name, pipeline_components,
                context_name, conversation_history, outcome,
                transfer_destination, error_message, tool_calls,
                avg_turn_latency_ms, max_turn_latency_ms, total_turns,
                caller_audio_format, codec_alignment_ok, barge_in_count,
                is_outbound, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, call_records)
        
        conn.commit()
        print("\n✅ Successfully seeded mock data to PostgreSQL!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error seeding data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_data()
