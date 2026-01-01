"""
Quick Setup Script for Supabase Storage Credentials
Run this after getting credentials from Supabase Dashboard
"""

import os

def update_env_file():
    """Interactive script to add Supabase Storage credentials to .env file"""
    
    print("=" * 60)
    print("🔧 Supabase Storage Configuration Setup")
    print("=" * 60)
    print("\nMake sure you have completed:")
    print("✅ Created 'eda-files' bucket in Supabase Dashboard")
    print("✅ Set bucket to Public")
    print("✅ Added storage policies (Public Access)")
    print("✅ Copied SUPABASE_URL and SUPABASE_KEY from Settings > API")
    print()
    
    # Get credentials from user
    supabase_url = input("Enter SUPABASE_URL (e.g., https://xxxxx.supabase.co): ").strip()
    supabase_key = input("Enter SUPABASE_KEY (the long anon/public key): ").strip()
    supabase_bucket = input("Enter SUPABASE_BUCKET [eda-files]: ").strip() or "eda-files"
    
    if not supabase_url or not supabase_key:
        print("\n❌ Error: URL and KEY are required!")
        return
    
    # Read existing .env file
    env_path = ".env"
    if not os.path.exists(env_path):
        print(f"\n❌ Error: {env_path} file not found!")
        print("Create it from .env.example first")
        return
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if Supabase credentials already exist
    has_supabase_url = any("SUPABASE_URL=" in line for line in lines)
    has_supabase_key = any("SUPABASE_KEY=" in line for line in lines)
    has_supabase_bucket = any("SUPABASE_BUCKET=" in line for line in lines)
    
    if has_supabase_url or has_supabase_key or has_supabase_bucket:
        print("\n⚠️ Warning: Supabase credentials already exist in .env file!")
        overwrite = input("Do you want to overwrite them? (yes/no): ").strip().lower()
        if overwrite != "yes":
            print("❌ Cancelled. No changes made.")
            return
        
        # Remove old Supabase lines
        lines = [line for line in lines if not any(key in line for key in ["SUPABASE_URL=", "SUPABASE_KEY=", "SUPABASE_BUCKET="])]
    
    # Add new Supabase credentials at the end
    lines.append("\n# Supabase Storage Configuration\n")
    lines.append(f"SUPABASE_URL={supabase_url}\n")
    lines.append(f"SUPABASE_KEY={supabase_key}\n")
    lines.append(f"SUPABASE_BUCKET={supabase_bucket}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(lines)
    
    print("\n✅ Successfully updated .env file!")
    print(f"   SUPABASE_URL: {supabase_url}")
    print(f"   SUPABASE_KEY: {supabase_key[:20]}...")
    print(f"   SUPABASE_BUCKET: {supabase_bucket}")
    print("\n📋 Next steps:")
    print("   1. Restart the backend server")
    print("   2. Run: python migrate_files_to_storage.py")
    print("   3. Test file upload in the web app")

if __name__ == "__main__":
    try:
        update_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
