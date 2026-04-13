#!/usr/bin/env python3
"""
ทดสอบการเชื่อมต่อ Database (SQLite และ PostgreSQL)

สคริปต์นี้ตรวจสอบว่าระบบสามารถเชื่อมต่อกับ database ที่กำหนดใน .env ได้หรือไม่

การใช้งาน:
    python scripts/test_database_connection.py
"""

import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from core.db_connection import get_db_connection, is_postgres, get_database_url


def test_connection():
    """ทดสอบการเชื่อมต่อ database"""
    
    print("=" * 70)
    print("ทดสอบการเชื่อมต่อ Database")
    print("=" * 70)
    
    # Check configuration
    db_url = get_database_url()
    is_pg = is_postgres()
    
    print(f"\n📋 Configuration:")
    print(f"   DATABASE_URL: {db_url if db_url else '(not set - using SQLite)'}")
    print(f"   Database Type: {'PostgreSQL' if is_pg else 'SQLite'}")
    
    if not is_pg:
        sqlite_path = os.getenv('CALL_HISTORY_DB_PATH', 'data/call_history.db')
        print(f"   SQLite Path: {sqlite_path}")
    
    # Test connection
    print(f"\n🔌 Testing connection...")
    
    try:
        conn = get_db_connection()
        print(f"   ✓ Connected successfully!")
        
        # Test query
        cursor = conn.cursor()
        
        if is_pg:
            # PostgreSQL version check
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            print(f"   ✓ PostgreSQL Version: {version[0] if version else 'Unknown'}")
            
            # Check tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"   ✓ Tables found: {len(tables)}")
            for table in tables:
                table_name = table[0] if isinstance(table, (list, tuple)) else table['table_name']
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()
                row_count = count[0] if isinstance(count, (list, tuple)) else count['count']
                print(f"      - {table_name}: {row_count} rows")
        else:
            # SQLite version check
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()
            print(f"   ✓ SQLite Version: {version[0]}")
            
            # Check tables
            cursor.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' 
                ORDER BY name
            """)
            tables = cursor.fetchall()
            print(f"   ✓ Tables found: {len(tables)}")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()
                print(f"      - {table_name}: {count[0]} rows")
        
        conn.close()
        
        print(f"\n✅ Database connection test PASSED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection test FAILED")
        print(f"   Error: {e}")
        print("=" * 70)
        logger.error("Connection test failed", exc_info=True)
        return False


def print_usage_guide():
    """แสดงวิธีการใช้งาน"""
    
    print("\n" + "=" * 70)
    print("📖 วิธีสลับระหว่าง SQLite และ PostgreSQL")
    print("=" * 70)
    
    print("\n1️⃣  ใช้งาน SQLite (ค่าเริ่มต้น):")
    print("   - ลบหรือ comment บรรทัด DATABASE_URL ใน .env")
    print("   - หรือเซ็ต: DATABASE_URL=")
    print("   - ระบบจะใช้ไฟล์: data/call_history.db")
    
    print("\n2️⃣  ใช้งาน PostgreSQL:")
    print("   - เซ็ต DATABASE_URL ใน .env:")
    print("   - DATABASE_URL=postgresql://user:pass@host:port/database")
    print("   - ตัวอย่าง:")
    print("     DATABASE_URL=postgresql://appuser:strongpassword123@192.168.38.46:5432/ava_db")
    
    print("\n3️⃣  Migrate ข้อมูลจาก SQLite ไป PostgreSQL:")
    print("   python scripts/migrate_sqlite_to_postgres.py")
    
    print("\n4️⃣  หลังจากเปลี่ยน DATABASE_URL:")
    print("   - Restart backend server")
    print("   - Restart main application")
    
    print("\n" + "=" * 70)


if __name__ == '__main__':
    success = test_connection()
    print_usage_guide()
    
    sys.exit(0 if success else 1)
