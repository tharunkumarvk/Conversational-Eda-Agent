# Google OAuth Setup Guide

## Step 1: Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create a New Project** (or select existing)
   - Click "Select a project" → "New Project"
   - Name: "EDA Agent" (or your preferred name)
   - Click "Create"

3. **Enable Google+ API**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - User Type: "External" → Click "Create"
     - App name: "EDA Agent"
     - User support email: your-email@gmail.com
     - Developer contact: your-email@gmail.com
     - Click "Save and Continue" → "Save and Continue" (skip scopes)
     - Add test users (your Gmail) → Click "Save and Continue"
     - Click "Back to Dashboard"

5. **Create OAuth Client ID**
   - Go back to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "EDA Agent Web Client"
   - **Authorized JavaScript origins:**
     - http://localhost:5173
     - http://localhost:5174
     - http://localhost:3000
   - **Authorized redirect URIs:**
     - http://localhost:5173
     - http://localhost:5174
     - http://localhost:3000
   - Click "Create"

6. **Copy Credentials**
   - Copy the **Client ID** (ends with `.apps.googleusercontent.com`)
   - Copy the **Client Secret**

## Step 2: Update .env File

Open `.env` file and update these lines:

```env
GOOGLE_CLIENT_ID=your-actual-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret-here
```

## Step 3: Restart Backend Server

After updating .env:
```bash
# Stop current backend (Ctrl+C in terminal)
# Start again:
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 4: Frontend Setup (Next Steps)

The frontend will automatically use the Google Client ID from the environment.

## Testing

Once set up:
1. Frontend will show "Sign in with Google" button
2. Click to authenticate with your Google account
3. After login, you'll get a JWT token
4. All API requests will be authenticated per user
5. Each user will see only their own data

## Security Notes

- **Never commit** actual credentials to git
- Use environment variables for all secrets
- The JWT_SECRET_KEY should be a long random string
- In production, use HTTPS and update redirect URIs accordingly
