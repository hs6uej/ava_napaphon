"""
Database connection abstraction layer.

Supports both SQLite and PostgreSQL based on DATABASE_URL environment variable.
Falls back to SQLite if DATABASE_URL is not set.
"""

import os
import logging
from typing import Any, Optional, Protocol
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DBConnection(Protocol):
    """Database connection protocol."""
    
    def cursor(self): ...
    def commit(self): ...
    def rollback(self): ...
    def close(self): ...
    def execute(self, sql: str, params: Any = None): ...


def get_database_url() -> Optional[str]:
    """Get database URL from environment."""
    return os.getenv("DATABASE_URL")


def is_postgres() -> bool:
    """Check if PostgreSQL is configured."""
    url = get_database_url()
    return url is not None and url.startswith(("postgres://", "postgresql://"))


def get_db_connection(db_path: Optional[str] = None, timeout: float = 30.0) -> DBConnection:
    """
    Get database connection based on DATABASE_URL environment variable.
    
    Args:
        db_path: SQLite database path (used only if DATABASE_URL is not set)
        timeout: Connection timeout in seconds
        
    Returns:
        Database connection (SQLite or PostgreSQL)
    """
    db_url = get_database_url()
    
    if db_url and db_url.startswith(("postgres://", "postgresql://")):
        # PostgreSQL connection
        try:
            import psycopg2
            import psycopg2.extras
            from urllib.parse import urlparse
            
            logger.debug(f"Connecting to PostgreSQL database db_url={db_url}")
            
            # Parse the URL
            parsed = urlparse(db_url)
            
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/') if parsed.path else 'postgres',
                user=parsed.username,
                password=parsed.password,
                connect_timeout=int(timeout)
            )
            
            # Use RealDictCursor for dict-like row access (similar to sqlite3.Row)
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            
            # Set autocommit off (we want explicit transactions)
            conn.autocommit = False
            
            return conn
            
        except ImportError:
            logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}", exc_info=True)
            raise
    else:
        # SQLite connection (fallback)
        import sqlite3
        from pathlib import Path
        
        db_path = db_path or os.getenv("CALL_HISTORY_DB_PATH", "data/call_history.db")
        
        logger.debug(f"Connecting to SQLite database: {db_path}")
        
        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(db_path, timeout=timeout, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrent read/write performance
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute(f"PRAGMA busy_timeout={int(timeout * 1000)};")
        conn.execute("PRAGMA foreign_keys=ON;")
        
        return conn


def adapt_sql_for_db(sql: str) -> str:
    """
    Adapt SQL for the current database type.
    
    Converts SQLite-specific syntax to PostgreSQL when needed.
    
    Args:
        sql: SQL query string
        
    Returns:
        Adapted SQL query
    """
    if not is_postgres():
        return sql
    
    # PostgreSQL adaptations
    adapted = sql
    
    # Replace INTEGER with SERIAL for auto-increment primary keys
    # (though we're using TEXT/UUID for PKs in this app)
    
    # Replace CURRENT_TIMESTAMP with NOW() if needed
    # Actually both DBs support CURRENT_TIMESTAMP, so no change needed
    
    # Replace || string concatenation if needed
    # Both DBs support ||, so no change needed
    
    # Replace SQLite's AUTOINCREMENT with PostgreSQL's SERIAL
    adapted = adapted.replace("AUTOINCREMENT", "")
    
    # Replace INTEGER column types with appropriate PostgreSQL types
    # Keep as-is since both support INTEGER
    
    return adapted


def get_placeholder_syntax() -> str:
    """
    Get the parameter placeholder syntax for the current database.
    
    Returns:
        '?' for SQLite, '%s' for PostgreSQL
    """
    return '%s' if is_postgres() else '?'


def adapt_placeholders(sql: str, params: tuple) -> tuple:
    """
    Adapt SQL placeholders and parameters for the current database.
    
    Args:
        sql: SQL query with ? placeholders
        params: Query parameters
        
    Returns:
        Tuple of (adapted_sql, params)
    """
    if not is_postgres():
        return sql, params
    
    # Convert ? to %s for PostgreSQL
    adapted_sql = sql.replace('?', '%s')
    
    return adapted_sql, params
