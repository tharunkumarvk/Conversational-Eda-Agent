"""
Migrate existing local files to Supabase Storage
This will upload all CSV files from uploaded_files/ and uploads/ to Supabase cloud
"""

import os
import sys
from sqlalchemy.orm import sessionmaker

try:
    from backend.db import engine, Dataset
    from backend.storage import init_storage, upload_file_to_storage
except ImportError:
    from db import engine, Dataset
    from storage import init_storage, upload_file_to_storage

def migrate_files_to_storage():
    """Migrate all existing local files to Supabase Storage"""
    
    print("=" * 60)
    print("📦 Migrating Local Files to Supabase Storage")
    print("=" * 60)
    
    # Initialize storage
    if not init_storage():
        print("\n❌ Failed to initialize Supabase Storage!")
        print("Make sure you have:")
        print("  1. Set SUPABASE_URL in .env")
        print("  2. Set SUPABASE_KEY in .env")
        print("  3. Created 'eda-files' bucket in Supabase")
        print("\nRun: python setup_storage_credentials.py")
        return
    
    # Connect to database
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all datasets
        datasets = session.query(Dataset).all()
        
        if not datasets:
            print("\n⚠️ No datasets found in database")
            return
        
        print(f"\nFound {len(datasets)} datasets to migrate\n")
        
        migrated = 0
        skipped = 0
        failed = 0
        
        for ds in datasets:
            print(f"Processing: {ds.filename}")
            
            # Check if file path is already a Supabase URL
            if ds.file_path and ds.file_path.startswith("http"):
                print(f"  ⏭️ Skipped (already in cloud): {ds.filename}")
                skipped += 1
                continue
            
            # Check if local file exists
            if not os.path.exists(ds.file_path):
                print(f"  ⚠️ Local file not found: {ds.file_path}")
                failed += 1
                continue
            
            # Read file content
            with open(ds.file_path, 'rb') as f:
                file_content = f.read()
            
            # Extract just the filename from the path (e.g., "uuid_filename.csv")
            storage_filename = os.path.basename(ds.file_path)
            
            # Upload to Supabase Storage
            success, result = upload_file_to_storage(
                file_content=file_content,
                filename=storage_filename,
                content_type="text/csv"
            )
            
            if success:
                # Update database with new URL
                old_path = ds.file_path
                ds.file_path = result  # Store the public URL
                session.commit()
                
                print(f"  ✅ Migrated: {storage_filename}")
                print(f"     Old: {old_path}")
                print(f"     New: {result}")
                migrated += 1
            else:
                print(f"  ❌ Failed: {result}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"✅ Migrated: {migrated}")
        print(f"⏭️ Skipped: {skipped}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(datasets)}")
        
        if migrated > 0:
            print("\n🎉 Migration completed!")
            print("\n📋 Next steps:")
            print("   1. Verify files in Supabase Dashboard > Storage > eda-files")
            print("   2. Restart the backend server")
            print("   3. Test file access in the web app")
            print("   4. Optionally delete local files from uploaded_files/")
        
    except Exception as e:
        print(f"\n❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    try:
        migrate_files_to_storage()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
