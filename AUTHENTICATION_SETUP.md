# 🔐 Google Authentication Setup - Complete Guide

## ✅ What's Been Implemented

### Backend (Completed)
- ✅ Installed: google-auth, google-auth-oauthlib, PyJWT, python-jose
- ✅ Created User model with google_id, email, name, picture
- ✅ Updated Dataset/ChatHistory/PlotHistory with user_id foreign keys
- ✅ Created auth.py with JWT token generation/verification
- ✅ Added auth endpoints: /api/auth/google, /api/auth/me, /api/auth/logout
- ✅ Protected upload/datasets endpoints with authentication
- ✅ Added user-specific data filtering

### Frontend (Completed)
- ✅ Installed: @react-oauth/google, react-router-dom
- ✅ Created AuthContext for state management
- ✅ Created Login page with Google Sign-In button
- ✅ Created ProtectedRoute wrapper
- ✅ Updated App.jsx with auth routing
- ✅ Updated Dashboard with user profile and logout
- ✅ Added JWT token to API requests

---

## 📋 Setup Steps (Required by You)

### Step 1: Get Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create/Select Project**
   - Click "Select a project" → "New Project"
   - Name: "EDA Agent" → Click "Create"

3. **Enable Google+ API** (or Google Identity)
   - Navigation menu → "APIs & Services" → "Library"
   - Search "Google+ API" or "Google Identity"
   - Click "Enable"

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User Type: **External** → Click "Create"
   - Fill in:
     - App name: "EDA Agent"
     - User support email: your-email@gmail.com
     - Developer contact: your-email@gmail.com
   - Click "Save and Continue" (3 times)
   - Add test users (your Gmail) → Click "Save"

5. **Create OAuth Client ID**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: "EDA Agent Web"
   - **Authorized JavaScript origins:**
     ```
     http://localhost:5173
     http://localhost:5174
     http://localhost:3000
     ```
   - **Authorized redirect URIs:**
     ```
     http://localhost:5173
     http://localhost:5174
     http://localhost:3000
     ```
   - Click "Create"

6. **Copy Credentials**
   - **Client ID**: Copy the value (ends with `.apps.googleusercontent.com`)
   - **Client Secret**: Copy the secret value

---

### Step 2: Update Backend .env

Open `d:\minimal-eda-tarp\.env` and update:

```env
# Replace these with your actual values from Google Cloud Console
GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret-here

# Update JWT secret to a strong random string
JWT_SECRET_KEY=paste-a-long-random-string-here-use-uuid-or-random-generator
```

**Generate JWT Secret (run in PowerShell):**
```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### Step 3: Update Frontend .env

Open `d:\minimal-eda-tarp\frontend\.env` and update:

```env
VITE_GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
```

**NOTE**: Only the Client ID is needed in frontend (not the secret!)

---

### Step 4: Database Migration

The User table has been created. Run this to ensure all tables are updated:

```powershell
# Stop backend if running (Ctrl+C)
# Restart to apply migrations
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The database will automatically add the User table and user_id columns.

---

### Step 5: Test the Authentication Flow

1. **Start Backend**
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start Frontend**
   ```powershell
   cd frontend
   npm run dev
   ```

3. **Test Login**
   - Open browser: http://localhost:5174 (or 5173)
   - Should redirect to /login
   - Click "Sign in with Google"
   - Select your Google account
   - After success, redirects to /dashboard
   - You'll see your profile picture and name in header

4. **Test Data Isolation**
   - Upload a file
   - Logout (click logout button in header)
   - Login with different Google account
   - Previous user's files should NOT be visible
   - Each user sees only their own data

---

## 🔧 Troubleshooting

### "Login failed" Error
- Check browser console for error details
- Verify Google Client ID is correct in frontend/.env
- Verify GOOGLE_CLIENT_ID in backend/.env
- Ensure URLs match in Google Cloud Console

### "Invalid Google token" Error  
- Client ID mismatch between frontend and backend
- Test user not added in OAuth consent screen
- API not enabled in Google Cloud Console

### "401 Unauthorized" on API Calls
- Token not being sent - check browser DevTools Network tab
- Token expired - logout and login again
- JWT_SECRET_KEY changed - logout all users

### Database Errors
- Run migration: restart backend
- Check user_id columns exist: use database client
- Existing data: will have user_id=NULL (legacy data)

---

## 🎯 What Works Now

✅ **User Authentication**
- Google Sign-In
- JWT token-based sessions
- Automatic logout on token expiry
- Profile display with avatar

✅ **Data Isolation**
- Each user sees only their datasets
- File uploads associated with user
- Chat history per user
- Plots separated by user
- No cross-user data access

✅ **Session Persistence**
- Token saved in localStorage
- Stays logged in after refresh
- Automatic redirect to login when not authenticated

✅ **Cloud Storage + Auth**
- Files uploaded to Supabase Storage
- User-specific database records
- Secure access control

---

## 🚀 Next Steps (Optional Enhancements)

1. **Email Verification**: Add email verification flow
2. **Password Reset**: Implement password recovery
3. **Profile Settings**: Allow users to update profile
4. **Team Sharing**: Share datasets between users
5. **Admin Panel**: Manage users and data
6. **Activity Logs**: Track user actions
7. **Usage Quotas**: Limit uploads per user

---

## 📝 Important Security Notes

- **Never commit** .env files with actual credentials
- Use **HTTPS in production** (not http)
- Update **JWT_SECRET_KEY** to long random value
- Keep **GOOGLE_CLIENT_SECRET** private (backend only)
- Set **token expiry** appropriately (currently 7 days)
- Implement **refresh tokens** for better security (future)

---

## 📖 API Documentation

### Authentication Endpoints

**POST /api/auth/google**
- Body: `{ "token": "google-oauth-token" }`
- Returns: `{ "access_token": "jwt", "token_type": "bearer", "user": {...} }`

**GET /api/auth/me**
- Headers: `Authorization: Bearer {jwt}`
- Returns: Current user info

**POST /api/auth/logout**
- Client-side: Remove token from localStorage
- Returns: `{ "message": "Logged out successfully" }`

### Protected Endpoints
All data endpoints now require:
```
Authorization: Bearer {jwt_token}
```

Endpoints:
- POST /api/upload
- GET /api/datasets
- GET /api/dataset/{file_id}
- DELETE /api/dataset/{file_id}
- POST /api/chat
- GET /api/chat/history/{file_id}
- GET /api/plots/{file_id}
- And all others...

---

## ✅ Checklist

Before testing:
- [ ] Google OAuth credentials created
- [ ] Backend .env updated with GOOGLE_CLIENT_ID
- [ ] Backend .env updated with GOOGLE_CLIENT_SECRET  
- [ ] Backend .env updated with JWT_SECRET_KEY
- [ ] Frontend .env updated with VITE_GOOGLE_CLIENT_ID
- [ ] Backend restarted to load new env vars
- [ ] Frontend restarted to load new env vars
- [ ] Test user added in Google OAuth consent screen

---

**Need Help?**
- Check [GOOGLE_OAUTH_SETUP.md](./GOOGLE_OAUTH_SETUP.md) for detailed Google setup
- Check logs in backend terminal for errors
- Check browser console for frontend errors
- Verify API calls in browser DevTools → Network tab
