#!/bin/bash
# Quick PostgreSQL Migration Setup Script
# This script helps you quickly set up and migrate to PostgreSQL

#PostgreSQL host [localhost]: 192.168.38.46
#PostgreSQL port [32857]: 5432
#PostgreSQL database name [ava_db]: 
#PostgreSQL username [postgres]: appuser
#PostgreSQL password: strongpassword123

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    AVA AI Voice Agent - PostgreSQL Migration Setup        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get PostgreSQL connection details
read -p "PostgreSQL host [localhost]: " PG_HOST
PG_HOST=${PG_HOST:-localhost}

read -p "PostgreSQL port [32857]: " PG_PORT
PG_PORT=${PG_PORT:-32857}

read -p "PostgreSQL database name [ava_db]: " PG_DATABASE
PG_DATABASE=${PG_DATABASE:-ava_db}

read -p "PostgreSQL username [postgres]: " PG_USER
PG_USER=${PG_USER:-postgres}

read -sp "PostgreSQL password: " PG_PASSWORD
echo ""

# Build DATABASE_URL
export DATABASE_URL="postgresql://${PG_USER}:${PG_PASSWORD}@${PG_HOST}:${PG_PORT}/${PG_DATABASE}"

echo ""
echo "Testing PostgreSQL connection..."

# Test connection using Python
python3 << 'EOF'
import psycopg2
from urllib.parse import urlparse
import sys
import os

try:
    url = os.environ['DATABASE_URL']
    parsed = urlparse(url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip('/'),
        user=parsed.username,
        password=parsed.password
    )
    conn.close()
    print("✓ Connection successful!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "Please check your PostgreSQL credentials and try again."
    exit 1
fi

echo ""
echo "Initializing PostgreSQL schema..."
python scripts/init_postgres_schema.py

if [ $? -ne 0 ]; then
    echo ""
    echo "✗ Schema initialization failed. Please check the error above."
    exit 1
fi

echo ""
read -p "Do you want to migrate existing SQLite data? [y/N]: " MIGRATE
if [[ "$MIGRATE" =~ ^[Yy]$ ]]; then
    read -p "SQLite database path [data/call_history.db]: " SQLITE_PATH
    SQLITE_PATH=${SQLITE_PATH:-data/call_history.db}
    
    export CALL_HISTORY_DB_PATH="$SQLITE_PATH"
    
    if [ ! -f "$SQLITE_PATH" ]; then
        echo "✗ SQLite database not found at: $SQLITE_PATH"
        echo "Skipping migration..."
    else
        echo ""
        echo "Starting migration from $SQLITE_PATH to PostgreSQL..."
        python scripts/migrate_sqlite_to_postgres.py
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Setup Complete!                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Add this to your .env file or environment:"
echo ""
echo "DATABASE_URL=\"$DATABASE_URL\""
echo ""
echo "To start using PostgreSQL, run:"
echo "  export DATABASE_URL=\"$DATABASE_URL\""
echo "  python main.py"
echo ""
