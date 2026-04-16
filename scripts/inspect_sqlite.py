import sqlite3

conn = sqlite3.connect('data/call_history.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    name = t[0]
    print(f"\n=== {name} ===")
    cursor.execute(f"PRAGMA table_info({name})")
    cols = cursor.fetchall()
    for col in cols:
        print(f"  {col}")
    cursor.execute(f"SELECT COUNT(*) FROM [{name}]")
    print(f"  Row count: {cursor.fetchone()[0]}")
    # Sample 2 rows
    cursor.execute(f"SELECT * FROM [{name}] LIMIT 2")
    rows = cursor.fetchall()
    col_names = [c[1] for c in cols]
    for row in rows:
        print(f"  Sample: {dict(zip(col_names, row))}")

conn.close()
