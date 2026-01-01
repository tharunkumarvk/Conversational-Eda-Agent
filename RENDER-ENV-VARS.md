# 🔐 Render Environment Variables Setup

## 📋 Copy these to your Render dashboard

Go to: **Render Dashboard → Your Service → Environment**

---

## ✅ Required Variables

```bash
# Google Gemini API (for AI features)
GOOGLE_API_KEY=<your-gemini-api-key>

# Google OAuth (for user authentication)
GOOGLE_CLIENT_ID=796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com

# Security Token (generate random 32+ character string)
JWT_SECRET_KEY=<generate-random-string>

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:BoffinBot%402004@db.lhwptjxktbhublymzdbp.supabase.co:5432/postgres

# Supabase Storage (for file uploads)
SUPABASE_URL=https://lhwptjxktbhublymzdbp.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
SUPABASE_BUCKET_NAME=EDA-Agent-Storage

# Frontend URL (add after Vercel deployment)
FRONTEND_URL=https://your-app.vercel.app
```

---

## 🔑 How to Get Each Value

### 1. **GOOGLE_API_KEY** (Gemini API)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key

### 2. **GOOGLE_CLIENT_ID** (OAuth)
Already provided: `796696929454-khst642g6005unc2ejhltv8id64j06t2.apps.googleusercontent.com`

### 3. **JWT_SECRET_KEY** (Security Token)
Generate a random string (32+ characters):
```bash
# In PowerShell:
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})

# Or use this online: https://randomkeygen.com/
```

### 4. **DATABASE_URL** (Supabase)
Already configured: `postgresql://postgres:BoffinBot%402004@db.lhwptjxktbhublymzdbp.supabase.co:5432/postgres`

### 5. **SUPABASE_URL**
Already configured: `https://lhwptjxktbhublymzdbp.supabase.co`

### 6. **SUPABASE_KEY** (Anon/Public Key)
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project: `lhwptjxktbhublymzdbp`
3. Go to **Settings → API**
4. Copy the **anon** / **public** key (starts with `eyJ...`)

### 7. **SUPABASE_BUCKET_NAME**
Already configured: `EDA-Agent-Storage`

### 8. **FRONTEND_URL**
- **Initial deployment**: Use `http://localhost:5173` (temporary)
- **After Vercel deployment**: Update with your Vercel URL (e.g., `https://your-app.vercel.app`)

---

## 📝 Step-by-Step in Render

1. Open **Render Dashboard** → Select your service
2. Click **"Environment"** tab (left sidebar)
3. Click **"Add Environment Variable"** for each variable above
4. **Key**: Variable name (e.g., `GOOGLE_API_KEY`)
5. **Value**: Your actual value
6. Click **"Save Changes"** at the bottom
7. ⚠️ **Service will auto-redeploy** after saving

---

## ⚠️ Common Issues

### Issue: "Network is unreachable" error
**Cause**: Missing DATABASE_URL environment variable

**Fix**: Ensure DATABASE_URL is set correctly in Render

### Issue: "Invalid credentials" on login
**Cause**: Missing GOOGLE_CLIENT_ID or incorrect value

**Fix**: Verify GOOGLE_CLIENT_ID matches the one in your .env file

### Issue: "File upload failed"
**Cause**: Missing SUPABASE_KEY or incorrect bucket name

**Fix**: 
1. Check SUPABASE_KEY in Supabase dashboard
2. Verify bucket `EDA-Agent-Storage` exists in Supabase Storage

---

## ✅ Verification

After setting all variables:

1. **Check deployment logs** in Render
2. Look for: `✅ Database connection established`
3. Visit: `https://your-backend.onrender.com/api/health`
4. Should return: `{"status": "ok"}`

---

## 🔄 Update FRONTEND_URL Later

**After deploying frontend to Vercel:**

1. Copy your Vercel URL: `https://your-app.vercel.app`
2. Go to **Render → Environment**
3. Update `FRONTEND_URL` value
4. Click **"Save Changes"** (triggers redeploy)

---

## 📚 Quick Reference

| Variable | Required? | Where to Get |
|----------|-----------|--------------|
| GOOGLE_API_KEY | ✅ Yes | Google AI Studio |
| GOOGLE_CLIENT_ID | ✅ Yes | Already provided |
| JWT_SECRET_KEY | ✅ Yes | Generate random string |
| DATABASE_URL | ✅ Yes | Already provided |
| SUPABASE_URL | ✅ Yes | Already provided |
| SUPABASE_KEY | ✅ Yes | Supabase Dashboard → API |
| SUPABASE_BUCKET_NAME | ✅ Yes | Already set: EDA-Agent-Storage |
| FRONTEND_URL | ⚠️ Later | Vercel URL after deployment |

---

**Next Step**: Go to Render and add these environment variables! 🚀
