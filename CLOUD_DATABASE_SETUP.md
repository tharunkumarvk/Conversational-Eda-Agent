# 🌐 Cloud Database Setup Guide

## Quick Start - Supabase (Recommended)

### 1. Create Supabase Account
1. Go to https://supabase.com
2. Click **"Start your project"**
3. Sign up with GitHub/Google
4. Click **"New Project"**
   - Organization: Choose or create
   - Name: `eda-agent-db`
   - Database Password: **Create strong password & SAVE IT!**
   - Region: Choose closest to you
   - Click **"Create new project"**
5. Wait 2-3 minutes for database provisioning

### 2. Get Connection String
1. In project dashboard → **Settings** (⚙️) → **Database**
2. Scroll to **"Connection string"** section
3. Select **"URI"** tab
4. Copy the connection string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual database password

### 3. Update Your .env File
```bash
# Open your .env file
notepad .env
```

Replace the DATABASE_URL line:
```env
# Change from:
DATABASE_URL=sqlite:///./backend/eda_agent.db

# To:
DATABASE_URL=postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres
```

### 4. Install PostgreSQL Driver
```bash
cd D:\minimal-eda-tarp
.\.venv\Scripts\activate
pip install psycopg2-binary
```

### 5. Migrate Your Data (Optional)
If you have existing data in SQLite:
```bash
python migrate_db.py
```

### 6. Restart Backend
```bash
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## ✅ Verification
1. Check backend logs for:
   ```
   INFO - Database: postgresql://postgres:***@db.xxxxx.supabase.co:5432/postgres
   ```
2. Upload a test file - it should save to cloud DB
3. Check Supabase dashboard → **Table Editor** to see your data

---

## Alternative: Neon Database

### 1. Create Neon Account
1. Go to https://neon.tech
2. Sign up with GitHub/Google
3. Create project: `eda-agent`
4. Copy connection string from dashboard

### 2. Update .env
```env
DATABASE_URL=postgresql://user:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
```

---

## Alternative: PlanetScale (MySQL)

### ⚠️ Note: Requires schema changes (MySQL vs SQLite differences)

1. Go to https://planetscale.com
2. Create database
3. Get connection string
4. Install MySQL driver: `pip install pymysql`
5. Update .env with MySQL URL

---

## Troubleshooting

### Error: "could not connect to server"
- Check your connection string is correct
- Ensure database password has no typos
- Verify your IP isn't blocked (Supabase allows all IPs by default)

### Error: "SSL connection required"
Add `?sslmode=require` to connection string:
```
postgresql://user:pass@host:5432/db?sslmode=require
```

### Error: "relation does not exist"
Tables not created. Run:
```bash
python migrate_db.py
```

### Check Current Database
```python
# In Python
from backend.config import settings
print(settings.DATABASE_URL)
```

---

## Benefits of Cloud Database

✅ **Data Persistence**: Survives server restarts
✅ **Scalability**: Handle more data & users
✅ **Backups**: Automatic backups on Supabase/Neon
✅ **Concurrent Access**: Multiple users can access simultaneously
✅ **Production Ready**: Deploy to Heroku/Railway/Vercel easily

---

## Cost

| Service | Free Tier | Storage | Limitations |
|---------|-----------|---------|-------------|
| **Supabase** | Forever | 500MB | Auto-pause after 7 days inactivity |
| **Neon** | Forever | 500MB | 3GB data transfer/month |
| **PlanetScale** | Forever | 5GB | 1B row reads/month |

All have generous free tiers perfect for development!
