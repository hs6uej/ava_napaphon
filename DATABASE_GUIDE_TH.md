# การใช้งาน Database (SQLite และ PostgreSQL)

ระบบรองรับทั้ง **SQLite** และ **PostgreSQL** โดยสามารถสลับได้ผ่านการตั้งค่าใน `.env`

## 📋 สถานะปัจจุบัน

ระบบได้รับการแก้ไขให้รองรับทั้ง 2 ฐานข้อมูลแล้ว:

✅ `src/core/db_connection.py` - ชั้น abstraction layer สำหรับทั้ง SQLite และ PostgreSQL  
✅ `src/core/call_history.py` - รองรับทั้ง 2 databases (cursor compatibility, placeholder syntax)  
✅ `src/core/outbound_store.py` - รองรับทั้ง 2 databases  
✅ `scripts/migrate_sqlite_to_postgres.py` - สำหรับ migrate ข้อมูล  
✅ `scripts/test_database_connection.py` - ทดสอบการเชื่อมต่อ

---

## 🔧 วิธีการใช้งาน

### 1️⃣ ใช้งาน SQLite (ค่าเริ่มต้น)

**ข้อดี:**
- ไม่ต้องติดตั้ง database server
- เหมาะสำหรับการทดสอบและ development
- ไฟล์เดียวพกพาสะดวก

**การตั้งค่า:**

ใน `.env` ให้ลบหรือ comment บรรทัด `DATABASE_URL`:

```bash
# DATABASE_URL=postgresql://user:pass@host:port/database
```

หรือเซ็ตให้เป็นค่าว่าง:

```bash
DATABASE_URL=
```

**ที่เก็บข้อมูล:**
- ค่าเริ่มต้น: `data/call_history.db`
- กำหนดเองได้ผ่าน: `CALL_HISTORY_DB_PATH=path/to/database.db`

---

### 2️⃣ ใช้งาน PostgreSQL (Production)

**ข้อดี:**
- รองรับ concurrent connections ได้มาก
- เหมาะสำหรับ production environment
- ประสิทธิภาพดีกว่าสำหรับข้อมูลจำนวนมาก
- มี replication และ backup ที่ดีกว่า

**การตั้งค่า:**

1. **ติดตั้ง PostgreSQL** (ถ้ายังไม่มี):
   ```bash
   # macOS
   brew install postgresql@15
   brew services start postgresql@15
   
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   sudo systemctl start postgresql
   ```

2. **สร้าง database และ user**:
   ```bash
   # เข้าสู่ PostgreSQL shell
   psql -U postgres
   
   # สร้าง user และ database
   CREATE USER appuser WITH PASSWORD 'strongpassword123';
   CREATE DATABASE ava_db OWNER appuser;
   GRANT ALL PRIVILEGES ON DATABASE ava_db TO appuser;
   \q
   ```

3. **ตั้งค่า DATABASE_URL ใน `.env`**:
   ```bash
   DATABASE_URL=postgresql://appuser:strongpassword123@localhost:5432/ava_db
   ```

   **รูปแบบ URL:**
   ```
   postgresql://username:password@host:port/database_name
   ```

   **ตัวอย่าง:**
   - Local: `postgresql://appuser:pass123@localhost:5432/ava_db`
   - Remote: `postgresql://appuser:pass123@192.168.1.100:5432/ava_db`
   - Docker: `postgresql://appuser:pass123@192.168.38.46:5432/ava_db`

---

## 🔄 การ Migrate ข้อมูลจาก SQLite ไป PostgreSQL

เมื่อต้องการย้ายข้อมูลจาก SQLite ไปยัง PostgreSQL:

### ขั้นตอน:

1. **ตรวจสอบว่ามีข้อมูลใน SQLite**:
   ```bash
   sqlite3 data/call_history.db "SELECT COUNT(*) FROM call_records;"
   ```

2. **ตั้งค่า DATABASE_URL ใน `.env`**:
   ```bash
   DATABASE_URL=postgresql://appuser:strongpassword123@localhost:5432/ava_db
   ```

3. **รัน migration script**:
   ```bash
   python scripts/migrate_sqlite_to_postgres.py
   ```

4. **ตรวจสอบผลลัพธ์**:
   - Script จะแสดง row count ของแต่ละตาราง
   - ตรวจสอบว่า SQLite และ PostgreSQL มีข้อมูลตรงกัน

### ตารางที่จะ Migrate:
- ✅ `call_records` - ประวัติการโทร
- ✅ `outbound_campaigns` - แคมเปญ outbound
- ✅ `outbound_leads` - รายชื่อผู้รับสาย
- ✅ `outbound_attempts` - ความพยายามโทร

---

## 🧪 ทดสอบการเชื่อมต่อ

ก่อนเริ่มใช้งาน ควรทดสอบการเชื่อมต่อก่อน:

```bash
python scripts/test_database_connection.py
```

**ผลลัพธ์ที่ควรได้:**
```
======================================================================
ทดสอบการเชื่อมต่อ Database
======================================================================

📋 Configuration:
   DATABASE_URL: postgresql://appuser:***@localhost:5432/ava_db
   Database Type: PostgreSQL

🔌 Testing connection...
   ✓ Connected successfully!
   ✓ PostgreSQL Version: PostgreSQL 15.x on ...
   ✓ Tables found: 4
      - call_records: 150 rows
      - outbound_attempts: 45 rows
      - outbound_campaigns: 3 rows
      - outbound_leads: 120 rows

✅ Database connection test PASSED
```

---

## ⚙️ การตั้งค่าเพิ่มเติม

### Environment Variables

```bash
# PostgreSQL
DATABASE_URL=postgresql://user:pass@host:port/database

# SQLite (ใช้เมื่อไม่มี DATABASE_URL)
CALL_HISTORY_DB_PATH=data/call_history.db
```

### ตรวจสอบว่าใช้ database อะไร

ใน code สามารถเช็คได้ว่าใช้ database แบบไหน:

```python
from core.db_connection import is_postgres

if is_postgres():
    print("Using PostgreSQL")
else:
    print("Using SQLite")
```

---

## 🔍 Troubleshooting

### ปัญหา: Connection failed

**SQLite:**
```bash
# ตรวจสอบว่าไฟล์มีอยู่
ls -la data/call_history.db

# ตรวจสอบ permissions
chmod 644 data/call_history.db
```

**PostgreSQL:**
```bash
# ทดสอบเชื่อมต่อ
psql -h localhost -U appuser -d ava_db

# ตรวจสอบว่า PostgreSQL ทำงานอยู่
pg_isready -h localhost -p 5432

# ตรวจสอบ logs
tail -f /usr/local/var/log/postgresql@15.log  # macOS
sudo tail -f /var/log/postgresql/postgresql-15-main.log  # Ubuntu
```

### ปัญหา: psycopg2 not installed

```bash
pip install psycopg2-binary
```

### ปัญหา: Migration ไม่สำเร็จ

1. ตรวจสอบว่า PostgreSQL database ว่างเปล่า
2. ลองรันอีกครั้ง (script จะล้างข้อมูลเดิมก่อน insert)
3. ตรวจสอบ logs เพื่อหาสาเหตุ

---

## 📊 เปรียบเทียบ SQLite vs PostgreSQL

| คุณสมบัติ | SQLite | PostgreSQL |
|-----------|--------|------------|
| **ติดตั้ง** | ไม่ต้องติดตั้ง | ต้องติดตั้ง server |
| **Concurrent Writes** | จำกัด | ดีมาก |
| **ขนาดข้อมูล** | เหมาะกับข้อมูลน้อย-กลาง | เหมาะกับข้อมูลมาก |
| **Performance** | ดีสำหรับ single user | ดีสำหรับ multi-user |
| **Backup** | Copy ไฟล์ | pg_dump / pg_restore |
| **Replication** | ไม่ได้ | รองรับ |
| **แนะนำสำหรับ** | Development, Testing | Production |

---

## 🚀 Best Practices

### Development:
- ใช้ SQLite เพื่อความสะดวก
- ไม่ต้องจัดการ database server

### Staging/Production:
- ใช้ PostgreSQL
- ตั้งค่า connection pooling
- สำรอง database เป็นประจำ
- ตั้งค่า monitoring

### Migration:
- ทดสอบใน staging environment ก่อน
- สำรอง SQLite ก่อน migrate
- Verify row counts หลัง migrate
- เก็บ SQLite backup ไว้สักระยะ

---

## 📝 สรุป

1. ✅ ระบบรองรับทั้ง SQLite และ PostgreSQL
2. ✅ สลับได้โดยเปลี่ยน `DATABASE_URL` ใน `.env`
3. ✅ มี migration script สำหรับย้ายข้อมูล
4. ✅ มี test script สำหรับทดสอบการเชื่อมต่อ
5. ✅ Code ใช้งานได้โดยอัตโนมัติทั้ง 2 แบบ

**หลังจากเปลี่ยน DATABASE_URL:**
- Restart backend server
- Restart main application
- ทดสอบการทำงาน

---

## 🆘 ขอความช่วยเหลือ

หากพบปัญหา:
1. ตรวจสอบ logs
2. รัน test script
3. ตรวจสอบ .env configuration
4. ตรวจสอบว่า PostgreSQL service ทำงานอยู่
