# 🚀 Quick Deployment Guide

## ✅ **Use: Vercel (Frontend) + Render (Backend)** - 100% FREE

---

## 📝 **Quick Steps**

### 1️⃣ **Push to GitHub**
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

---

### 2️⃣ **Deploy Backend (Render.com)**

1. Sign up at **[render.com](https://render.com)** with GitHub
2. Click **"New +" → "Web Service"**
3. Select your repository
4. Configure:
   - **Name**: `eda-agent-backend`
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add these **Environment Variables**:
   ```
   GOOGLE_API_KEY=<your-gemini-key>
   GOOGLE_CLIENT_ID=796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com
   JWT_SECRET_KEY=<generate-random-32-char-string>
   DATABASE_URL=postgresql://postgres:BoffinBot%402004@db.lhwptjxktbhublymzdbp.supabase.co:5432/postgres
   SUPABASE_URL=https://lhwptjxktbhublymzdbp.supabase.co
   SUPABASE_KEY=<your-supabase-key>
   SUPABASE_BUCKET_NAME=EDA-Agent-Storage
   FRONTEND_URL=<will-add-after-step-3>
   ```
6. Click **"Create Web Service"**
7. **Copy your backend URL**: `https://eda-agent-backend.onrender.com`

---

### 3️⃣ **Deploy Frontend (Vercel.com)**

1. Sign up at **[vercel.com](https://vercel.com)** with GitHub
2. Click **"Add New..." → "Project"**
3. Select your repository
4. Configure:
   - **Framework**: Vite
   - **Root Directory**: `frontend`
5. Add these **Environment Variables**:
   ```
   VITE_API_URL=https://eda-agent-backend.onrender.com
   VITE_GOOGLE_CLIENT_ID=796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com
   ```
6. Click **"Deploy"**
7. **Copy your frontend URL**: `https://your-app.vercel.app`

---

### 4️⃣ **Update Backend with Frontend URL**

1. Go to **Render** → Your service → **Environment**
2. Update `FRONTEND_URL` with your Vercel URL
3. Save (auto-redeploys)

---

### 5️⃣ **Update Google OAuth**

1. Go to **[Google Cloud Console](https://console.cloud.google.com/apis/credentials)**
2. Select your OAuth Client
3. Add **Authorized origins**:
   ```
   https://your-app.vercel.app
   https://eda-agent-backend.onrender.com
   ```
4. Add **Redirect URIs**:
   ```
   https://your-app.vercel.app/login
   ```
5. Save

---

## ✅ **Done! Your app is live!**

Visit: `https://your-app.vercel.app`

---

## 💡 **Pro Tip**

**Keep backend alive** (prevent 30s cold starts):
- Sign up at [UptimeRobot.com](https://uptimerobot.com) (free)
- Add monitor: Ping `https://eda-agent-backend.onrender.com/docs` every 5 minutes

---

## 📊 **Free Tier Limits**

- **Vercel**: Unlimited bandwidth, 100 deployments/day
- **Render**: 750 hours/month, spins down after 15min inactivity
- **Supabase**: 500MB database, 1GB storage

---

For detailed instructions, see: **[DEPLOYMENT.md](./DEPLOYMENT.md)**
