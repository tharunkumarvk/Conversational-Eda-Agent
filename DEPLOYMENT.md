# 🚀 Deployment Guide - EDA Agent

## ✅ **Recommended: Vercel (Frontend) + Render (Backend)**

This is **100% FREE** and the easiest option with great performance.

---

## 📦 **Step-by-Step Deployment**

### **STEP 1: Prepare Your Repository**

1. **Push your code to GitHub** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

---

### **STEP 2: Deploy Backend on Render**

1. **Go to [render.com](https://render.com)** and sign up with GitHub

2. **Click "New +" → "Web Service"**

3. **Connect your GitHub repository**

4. **Configure the service:**
   - **Name**: `eda-agent-backend` (or your choice)
   - **Root Directory**: Leave blank
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

5. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):
   ```
   GOOGLE_API_KEY=AIzaSyATuaqXk4HAUfoy...
   GOOGLE_CLIENT_ID=796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com
   JWT_SECRET_KEY=your_super_secret_key_at_least_32_characters_long
   DATABASE_URL=postgresql://postgres:BoffinBot%402004@db.lhwptjxktbhublymzdbp.supabase.co:5432/postgres
   SUPABASE_URL=https://lhwptjxktbhublymzdbp.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_BUCKET_NAME=EDA-Agent-Storage
   FRONTEND_URL=https://your-app.vercel.app
   ```
   *(We'll update FRONTEND_URL in Step 4)*

6. **Click "Create Web Service"**

7. **Wait 5-10 minutes** for deployment. Your backend URL will be:
   ```
   https://eda-agent-backend.onrender.com
   ```
   **📝 Copy this URL!**

---

### **STEP 3: Deploy Frontend on Vercel**

1. **Go to [vercel.com](https://vercel.com)** and sign up with GitHub

2. **Click "Add New..." → "Project"**

3. **Import your GitHub repository**

4. **Configure the project:**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (auto-detected)
   - **Output Directory**: `dist` (auto-detected)
   - **Install Command**: `npm install` (auto-detected)

5. **Add Environment Variables:**
   ```
   VITE_API_URL=https://eda-agent-backend.onrender.com
   VITE_GOOGLE_CLIENT_ID=796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com
   ```
   *(Use the backend URL from Step 2)*

6. **Click "Deploy"**

7. **Wait 2-3 minutes**. Your frontend URL will be:
   ```
   https://your-app-name.vercel.app
   ```
   **📝 Copy this URL!**

---

### **STEP 4: Update Backend with Frontend URL**

1. **Go back to Render dashboard** → Your backend service

2. **Go to "Environment" tab**

3. **Update the `FRONTEND_URL` variable** with your Vercel URL:
   ```
   FRONTEND_URL=https://your-app-name.vercel.app
   ```

4. **Click "Save Changes"** (backend will auto-redeploy)

---

### **STEP 5: Update Google OAuth Settings**

1. **Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)**

2. **Select your OAuth 2.0 Client ID**

3. **Add Authorized JavaScript origins:**
   ```
   https://your-app-name.vercel.app
   https://eda-agent-backend.onrender.com
   ```

4. **Add Authorized redirect URIs:**
   ```
   https://your-app-name.vercel.app/login
   https://your-app-name.vercel.app/dashboard
   ```

5. **Click "Save"**

---

## ✅ **That's It! Your App is Live!**

### **URLs:**
- **Frontend**: `https://your-app-name.vercel.app`
- **Backend**: `https://eda-agent-backend.onrender.com`
- **API Docs**: `https://eda-agent-backend.onrender.com/docs`

---

## 🔧 **Important Notes**

### **Render Free Tier:**
- Backend **spins down after 15 minutes** of inactivity
- First request after spin-down takes **~30 seconds** (cold start)
- 750 hours/month free (always-on for 31 days)

### **Vercel Free Tier:**
- Unlimited bandwidth
- 100 deployments/day
- Always-on (no cold starts)

---

## 🔄 **Automatic Deployments**

Both Vercel and Render will **automatically redeploy** when you push to GitHub:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

- **Vercel**: Redeploys in ~2 minutes
- **Render**: Redeploys in ~5-10 minutes

---

## 🐛 **Troubleshooting**

### **Backend not responding:**
- Check Render logs: Dashboard → Your service → Logs
- Verify environment variables are set correctly
- Wait for cold start (~30 seconds)

### **Frontend can't connect to backend:**
- Verify `VITE_API_URL` matches your Render URL
- Check browser console for CORS errors
- Ensure `FRONTEND_URL` is set in backend env vars

### **Google OAuth not working:**
- Verify both URLs are added to Google Cloud Console
- Clear browser cache and try again
- Check that client ID matches in both frontend and backend

---

## 💡 **Pro Tips**

1. **Keep Backend Active**: Render free tier spins down. Use [UptimeRobot](https://uptimerobot.com) (free) to ping your backend every 5 minutes to keep it alive.

2. **Custom Domain**: Both Vercel and Render support free custom domains:
   - Vercel: Dashboard → Your project → Settings → Domains
   - Render: Dashboard → Your service → Settings → Custom Domain

3. **Monitor Logs**:
   - Vercel: Deployment logs in dashboard
   - Render: Real-time logs in dashboard

4. **Environment Variables**: Never commit `.env` files to Git. Always use platform environment variables.

---

## 🎉 **Success!**

Your EDA Agent is now deployed and accessible worldwide! Share your URL with others! 🚀
