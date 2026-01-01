# 🗄️ Supabase Storage Setup Guide

## Step 1: Create Storage Bucket in Supabase Dashboard

### 1.1 Go to Supabase Dashboard
1. Open your browser and go to: https://supabase.com/dashboard
2. Login with your account
3. Select your project: **lhwptjxktbhublymzdbp**

### 1.2 Create Storage Bucket
1. In the left sidebar, click **"Storage"**
2. Click **"New bucket"** button (green button at top right)
3. Fill in the bucket details:
   ```
   Name: eda-files
   Public bucket: ✅ YES (check this box)
   File size limit: 52428800 (50 MB)
   Allowed MIME types: Leave empty (allows all types)
   ```
4. Click **"Create bucket"**

### 1.3 Set Bucket Permissions (IMPORTANT!)
1. Click on your new **"eda-files"** bucket
2. Click **"Policies"** tab at the top
3. Click **"New Policy"** button
4. Click **"For full customization"** (or "Get started quickly" → "Enable access to all users")
5. **For Development (Easy Option):**
   - Policy Name: `Public Access`
   - Target Roles: `public`
   - Check all boxes: SELECT, INSERT, UPDATE, DELETE
   - Click **"Save"**

   **For Production (Secure Option):**
   - Create separate policies for authenticated users only
   - We can set this up later

### 1.4 Get API Keys
1. In the left sidebar, click **"Settings"** (gear icon at bottom)
2. Click **"API"** section
3. You'll need TWO values:

   **Copy these:**
   ```
   Project URL: https://lhwptjxktbhublymzdbp.supabase.co
   anon/public key: (long string starting with "eyJ...")
   ```

   **Example format:**
   ```
   URL: https://lhwptjxktbhublymzdbp.supabase.co
   Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6...
   ```

## Step 2: Update Your Project Configuration

### 2.1 Add Credentials to .env File
You'll add these to your `.env` file:
```env
# Supabase Storage Configuration
SUPABASE_URL=https://lhwptjxktbhublymzdbp.supabase.co
SUPABASE_KEY=your_anon_public_key_here
SUPABASE_BUCKET=eda-files
```

### 2.2 Install Required Package
I'll install the Supabase Python client automatically.

## Step 3: How It Will Work

### Before (Current - Local Storage):
```
User uploads file.csv
    ↓
Saved to: D:\minimal-eda-tarp\uploaded_files\uuid_file.csv ❌ (local only)
    ↓
Database: Stores local file path
```

### After (Supabase Storage):
```
User uploads file.csv
    ↓
Uploaded to: Supabase Storage Cloud ✅ (accessible anywhere)
    ↓
Database: Stores Supabase Storage URL
    ↓
Processing: Download temporarily → Process → Delete temp file
```

## Step 4: Verify Storage is Working

After setup, you can verify in Supabase Dashboard:
1. Go to **Storage** → **eda-files** bucket
2. You should see uploaded files listed with their UUIDs
3. Click any file to get its public URL
4. Files are accessible from anywhere!

## Benefits of Supabase Storage

✅ **True Multi-User Access**
- Files stored in cloud, not local disk
- Any user can access any file from anywhere
- Perfect for deployment

✅ **No Server Disk Space Issues**
- Files stored in Supabase's infrastructure
- No need to manage local disk space

✅ **Built-in CDN**
- Fast file delivery worldwide
- Automatic caching

✅ **Easy Deployment**
- Deploy backend to Heroku/Railway/Vercel
- Files automatically accessible

✅ **Backup & Security**
- Supabase handles backups
- Configurable access policies

## Free Tier Limits

Supabase Free Tier includes:
- **1 GB storage** (plenty for CSV files)
- **2 GB bandwidth per month**
- **50 MB max file size**

## Next Steps

1. Complete Steps 1.1-1.4 above to get your Supabase credentials
2. Copy the **SUPABASE_URL** and **SUPABASE_KEY** 
3. Tell me when you have them, and I'll update your `.env` file
4. I'll then migrate all existing files to the cloud automatically!

---

**Need Help?**
- If you get stuck on any step, let me know which step number
- I can provide screenshots guidance if needed
- Common issue: Forgot to make bucket "Public" → Go back to Step 1.3
