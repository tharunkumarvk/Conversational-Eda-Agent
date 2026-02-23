# 🚀 Quick Start - Local Development

## **Option 1: SQLite (Easiest - No Setup Required)**

### 1. Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./streamlit_users.db
```

### 2. Run the app:
```bash
streamlit run eda_agent_agentic.py
```

That's it! The database file will be created automatically.

---

## **Option 2: MySQL on Your Laptop**

### 1. Install MySQL:
**Windows:**
- Download from: https://dev.mysql.com/downloads/installer/
- Run installer, choose "Developer Default"
- Set root password during installation

**Mac:**
```bash
brew install mysql
brew services start mysql
```

**Linux:**
```bash
sudo apt-get install mysql-server
sudo systemctl start mysql
```

### 2. Create Database:
```bash
# Login to MySQL
mysql -u root -p

# In MySQL console:
CREATE DATABASE eda_database;
CREATE USER 'eda_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON eda_database.* TO 'eda_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=mysql+pymysql://eda_user:your_secure_password@localhost:3306/eda_database
```

### 4. Run the app:
```bash
streamlit run eda_agent_agentic.py
```

---

## **Option 3: Cloud Database (PlanetScale - Free Forever)**

### Why PlanetScale?
- ✅ Free 5GB storage
- ✅ No credit card required
- ✅ Always online
- ✅ Works for deployment too!

### Setup:
1. Go to [planetscale.com](https://planetscale.com)
2. Sign up (free)
3. Create new database
4. Get connection string from "Connect" button
5. Copy the string (looks like: `mysql+pymysql://user:pass@aws.connect.psdb.cloud/...`)

### Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=your_planetscale_connection_string
```

### Run the app:
```bash
streamlit run eda_agent_agentic.py
```

---

## 🎯 **First Time Running the App**

1. Open http://localhost:8501
2. Click **"Sign Up"** tab
3. Create your account:
   - Full Name
   - Email
   - Username
   - Password (min 8 chars, with uppercase, lowercase, number)
4. Click **"Create Account"**
5. Switch to **"Login"** tab
6. Login with your credentials
7. Start analyzing data! 🎉

---

## 📊 **Test the App**

Try uploading a CSV file from the `data/` folder or use these test datasets:
- `uploaded_files/132ddf8c-3c45-47c6-af4d-392e0652da94_orders.csv`
- `uploads/iris.csv`

---

## ❓ **Troubleshooting**

### "ModuleNotFoundError: No module named 'bcrypt'"
```bash
pip install bcrypt
```

### "ModuleNotFoundError: No module named 'pymysql'"
```bash
pip install pymysql
```

### "Can't connect to MySQL server"
- Check MySQL is running: `systemctl status mysql` (Linux) or check Services (Windows)
- Verify username/password in `.env` file
- Try `mysql -u eda_user -p` to test connection

### "Table doesn't exist" or "Access denied"
The tables are created automatically on first run. If you see this error:
1. Make sure the database exists
2. Grant full permissions to the user
3. Restart the app

---

## 🔄 **Switch Between Database Types**

Just change the `DATABASE_URL` in your `.env` file:

```env
# SQLite (local file)
DATABASE_URL=sqlite:///./streamlit_users.db

# MySQL local
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/dbname

# PlanetScale cloud
DATABASE_URL=mysql+pymysql://user:pass@aws.connect.psdb.cloud/dbname?ssl_ca=...

# Supabase cloud
DATABASE_URL=postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres
```

Each database type will work identically!

---

## 📋 **Next Steps**

- ✅ Got it working locally? → See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) to deploy
- ✅ Want to customize? → Edit `streamlit_login.py` for UI changes
- ✅ Add features? → Check `streamlit_auth.py` for auth functions

**Enjoy your authenticated EDA app! 🚀**
