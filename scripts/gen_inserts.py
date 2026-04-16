import sqlite3, json

conn = sqlite3.connect('data/call_history.db')
cur = conn.cursor()
cur.execute("SELECT * FROM call_records LIMIT 5")
rows = cur.fetchall()
cols = [d[0] for d in cur.description]
col_csv = ", ".join(cols)

for row in rows:
    vals = []
    for v in row:
        if v is None:
            vals.append("NULL")
        elif isinstance(v, (int, float)):
            vals.append(str(v))
        else:
            escaped = str(v).replace("'", "''")
            vals.append("'{}'".format(escaped))
    print("INSERT INTO call_records ({}) VALUES ({}) ON CONFLICT (id) DO NOTHING;".format(col_csv, ", ".join(vals)))

conn.close()
