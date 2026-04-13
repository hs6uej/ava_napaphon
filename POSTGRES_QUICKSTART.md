# PostgreSQL Migration - Quick Reference

## ✅ Migration Complete!

Your AVA AI Voice Agent now supports PostgreSQL on **localhost:32857**

---

## 🚀 Quick Start

### Step 1: Configure Database Connection

```bash
export DATABASE_URL="postgresql://your_user:your_password@localhost:32857/ava_db"
```

### Step 2: Initialize Schema

```bash
python scripts/init_postgres_schema.py
```

### Step 3: (Optional) Migrate Existing Data

```bash
export CALL_HISTORY_DB_PATH="data/call_history.db"
python scripts/migrate_sqlite_to_postgres.py
```

### Step 4: Start Application

```bash
python main.py
```

---

## 📋 What Was Created

| File | Purpose |
|------|---------|
| `src/core/db_connection.py` | Database abstraction layer |
| `src/core/db_schema_postgres.py` | PostgreSQL schema |
| `scripts/init_postgres_schema.py` | Schema initialization |
| `scripts/migrate_sqlite_to_postgres.py` | Data migration tool |
| `scripts/setup_postgres.sh` | Interactive setup wizard |
| `docs/POSTGRESQL_MIGRATION.md` | Full migration guide |

## 📊 Database Tables

✅ **call_records** - Call history and analytics  
✅ **outbound_campaigns** - Dialing campaigns  
✅ **outbound_leads** - Campaign contacts  
✅ **outbound_attempts** - Call attempts  

---

## 🔧 Interactive Setup (Easiest)

```bash
./scripts/setup_postgres.sh
```

This wizard will:
- Test your PostgreSQL connection
- Initialize the schema
- Optionally migrate your SQLite data

---

## 🔄 Switch Between Databases

### Use PostgreSQL:
```bash
export DATABASE_URL="postgresql://user:pass@localhost:32857/ava_db"
```

### Use SQLite:
```bash
unset DATABASE_URL
```

---

## ✅ Verify Installation

Check tables were created:
```bash
psql -h localhost -p 32857 -U your_user -d ava_db -c "\dt"
```

Check row counts:
```bash
psql -h localhost -p 32857 -U your_user -d ava_db -c "
SELECT 'call_records' as table, COUNT(*) FROM call_records UNION ALL
SELECT 'outbound_campaigns', COUNT(*) FROM outbound_campaigns UNION ALL
SELECT 'outbound_leads', COUNT(*) FROM outbound_leads UNION ALL
SELECT 'outbound_attempts', COUNT(*) FROM outbound_attempts;"
```

---

## 📖 Documentation

- **Full Guide**: [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md)
- **Summary**: [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md)

---

## 🆘 Troubleshooting

### Can't connect to PostgreSQL?
1. Check PostgreSQL is running: `pg_isready -h localhost -p 32857`
2. Verify credentials in DATABASE_URL
3. Check firewall allows port 32857

### Authentication failed?
- Verify username and password
- Try connecting with `psql` directly first

### Import errors?
```bash
pip install -r requirements.txt
```

---

## 🎯 Next Steps

1. **Configure your DATABASE_URL** with actual credentials
2. **Run the schema initialization** (required)
3. **Migrate data** if you have existing SQLite database
4. **Start your application** and verify it connects

**Need help?** See [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md) for detailed instructions.
