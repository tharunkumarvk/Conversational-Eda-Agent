# 🚀 Deployment Guide - DataColombus Streamlit App

This guide will help you deploy your authenticated Streamlit EDA app for free!

---

## 📋 **Quick Overview**

Your app now has:
- ✅ **Email/Password Authentication** 
- ✅ **User-specific data isolation**
- ✅ **Flexible database support** (MySQL, PostgreSQL, SQLite)
- ✅ **Cloud-ready configuration**

---

## 🏠 **Local Development Setup**

### **Step 1: Install Dependencies**

```bash
# Activate your virtual environment (if you have one)
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Database (Choose ONE option)**

#### **Option A: SQLite (Easiest - for testing)**
Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=sqlite:///./streamlit_users.db
```

#### **Option B: MySQL on Your Laptop**
1. Install MySQL if not already installed
2. Create a database:
```sql
CREATE DATABASE eda_database;
CREATE USER 'eda_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON eda_database.* TO 'eda_user'@'localhost';
FLUSH PRIVILEGES;
```

3. Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=mysql+pymysql://eda_user:your_password@localhost:3306/eda_database
```

#### **Option C: Cloud Database (PlanetScale - Free MySQL)**
1. Go to [planetscale.com](https://planetscale.com) → Sign up
2. Create new database
3. Get connection string
4. Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key
DATABASE_URL=mysql+pymysql://username:password@aws.connect.psdb.cloud/database_name?ssl_ca=/etc/ssl/certs/ca-certificates.crt
```

### **Step 3: Run Locally**

```bash
streamlit run eda_agent_agentic.py
```

Open http://localhost:8501 and create your account!

---

## ☁️ **Cloud Deployment (FREE on Streamlit Cloud)**

### **Prerequisites:**
1. ✅ GitHub account
2. ✅ Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
3. ✅ Cloud database (PlanetScale or Supabase - both FREE)

---

### **Step 1: Setup Cloud Database**

#### **Option A: PlanetScale (MySQL - Recommended)**

1. **Create Account:** [planetscale.com](https://planetscale.com)
2. **Create Database:**
   - Click "New Database"
   - Name: `eda-database`
   - Region: Choose closest to you
   - Click "Create database"

3. **Get Connection String:**
   - Go to "Connect" → "Connect with" → "Python"
   - Copy the connection string
   - It looks like: `mysql+pymysql://user:pass@aws.connect.psdb.cloud/dbname?ssl_ca=...`

4. **Save for Later:** You'll need this for Streamlit secrets

#### **Option B: Supabase (PostgreSQL - Alternative)**

1. **Create Account:** [supabase.com](https://supabase.com)
2. **Create Project:**
   - Click "New Project"
   - Set database password (save it!)
   - Wait for setup (~2 minutes)

3. **Get Connection String:**
   - Go to Settings → Database
   - Find "Connection String" → "URI"
   - Copy it (replace `[YOUR-PASSWORD]` with your actual password)
   - Format: `postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres`

4. **Save for Later:** You'll need this for Streamlit secrets

---

### **Step 2: Push Code to GitHub**

```bash
# Initialize git (if not already)
git init

# Add files
git add .
git commit -m "Add authentication to Streamlit app"

# Create repository on GitHub (via website)
# Then push:
git remote add origin https://github.com/yourusername/your-repo.git
git branch -M main
git push -u origin main
```

---

### **Step 3: Deploy on Streamlit Cloud**

1. **Go to:** [share.streamlit.io](https://share.streamlit.io)

2. **Sign in with GitHub**

3. **Create New App:**
   - Repository: Select your repository
   - Branch: `main`
   - Main file path: `eda_agent_agentic.py`
   - Click "Advanced settings"

4. **Add Secrets:**
   Click "Advanced settings" → "Secrets"
   
   Paste this (replace with YOUR values):
   
   ```toml
   # Google Gemini API Key
   GOOGLE_API_KEY = "your_actual_gemini_api_key"
   
   # Database - Use YOUR cloud database connection string
   # For PlanetScale (MySQL):
   DATABASE_URL = "mysql+pymysql://user:pass@aws.connect.psdb.cloud/dbname?ssl_ca=/etc/ssl/certs/ca-certificates.crt"
   
   # OR for Supabase (PostgreSQL):
   # DATABASE_URL = "postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"
   ```

5. **Click "Deploy"**

Wait 2-3 minutes for deployment to complete!

---

## 🎉 **Your App is Live!**

Your app will be available at: `https://yourusername-your-repo-name.streamlit.app`

**Share this URL with anyone!** They can:
- ✅ Create their own account
- ✅ Upload and analyze their data
- ✅ All data is private and isolated per user

---

## 🔐 **Security Notes**

1. **Never commit `.env` or `secrets.toml`** - They're in `.gitignore`
2. **User passwords are hashed** with bcrypt
3. **Sessions expire after 7 days**
4. **Each user's data is completely isolated**

---

## 📊 **Free Tier Limits**

| Service | Free Tier | Usage |
|---------|-----------|-------|
| **Streamlit Cloud** | 1 app, unlimited users | ✅ Perfect! |
| **PlanetScale** | 5GB storage, 1B rows/month | ✅ More than enough |
| **Supabase** | 500MB DB, 1GB storage | ✅ Good for start |
| **Google Gemini** | 60 requests/min | ✅ Great |

---

## 🐛 **Troubleshooting**

### **"Database connection failed"**
- Check your `DATABASE_URL` in secrets
- Ensure database is running and accessible
- For PlanetScale: Enable "Connect from anywhere"

### **"GOOGLE_API_KEY not found"**
- Add it to `.streamlit/secrets.toml` (local) or Streamlit Cloud secrets
- Get key from: https://makersuite.google.com/app/apikey

### **"Module not found"**
- Ensure `requirements.txt` is in root directory
- Streamlit Cloud will auto-install dependencies

### **Can't create account**
- Check database connection
- Ensure tables are created (automatic on first run)

---

## 📱 **Next Steps**

1. ✅ Create your admin account first
2. ✅ Test uploading a CSV file
3. ✅ Try the AI chat features
4. ✅ Share the URL with friends/colleagues!

---

## 🔄 **Updating Your Deployed App**

Just push to GitHub:
```bash
git add .
git commit -m "Your update message"
git push
```

Streamlit Cloud will auto-deploy the changes in ~2 minutes!

---

## 💡 **Tips**

- **Free MySQL with more space?** Use PlanetScale instead of Supabase
- **Want file uploads to persist?** Set up Supabase Storage (also free)
- **Need more API calls?** Google Gemini has generous free tier
- **Multiple apps?** Deploy on [Railway](https://railway.app) or [Render](https://render.com)

---

## 🆘 **Need Help?**

- Streamlit Community: [discuss.streamlit.io](https://discuss.streamlit.io)
- PlanetScale Docs: [docs.planetscale.com](https://docs.planetscale.com)
- Supabase Docs: [supabase.com/docs](https://supabase.com/docs)

---

**Happy Deploying! 🚀**
