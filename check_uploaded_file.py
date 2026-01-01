"""Check the most recently uploaded file in database"""
from backend.db import SessionLocal
from backend.db import Dataset

with SessionLocal() as db:
    # Check specifically for the test file we just uploaded
    test_file_id = "9de7e43d-245b-4821-9c3d-e50e49ee9624"
    result = db.query(Dataset).filter(Dataset.file_id == test_file_id).first()
    
    if result:
        print(f"Test file found!")
        print(f"File ID: {result.file_id}")
        print(f"Filename: {result.filename}")
        print(f"File Path: {result.file_path}")
        print()
        if result.file_path.startswith('http'):
            print("✅ Stored as CLOUD URL")
            print(f"🌐 Supabase Storage URL: {result.file_path}")
        else:
            print("❌ Stored as local path")
    else:
        print(f"Test file {test_file_id} not found in database")
        
    print("\n" + "="*50)
    print("All files in database (most recent first):")
    print("="*50)
    files = db.query(Dataset).order_by(Dataset.upload_time.desc()).limit(5).all()
    for f in files:
        storage_type = "CLOUD" if f.file_path.startswith('http') else "LOCAL"
        print(f"[{storage_type}] {f.filename} - {f.file_id[:8]}...")
