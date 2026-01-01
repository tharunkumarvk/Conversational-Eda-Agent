from supabase import create_client
import sys

client = create_client(
    'https://lhwptjxktbhublymzdbp.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxod3B0anhrdGJodWJseW16ZGJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcyMzgyMDYsImV4cCI6MjA4MjgxNDIwNn0.nzyyASBWdxCSQ0vc0AseahQmLaBvWCdJ5WIWWVp30Wk'
)

bucket_names = ["EDA-AGENT-STORAGE", "eda-agent-storage", "Eda-Agent-Storage"]
test_data = b"test,data\n1,2"

for bucket_name in bucket_names:
    print(f"\n{'='*60}")
    print(f"Testing bucket: {bucket_name}")
    print(f"{'='*60}")
    
    try:
        response = client.storage.from_(bucket_name).upload(
            path=f"test_{bucket_name}.csv",
            file=test_data,
            file_options={"content-type": "text/csv", "upsert": "true"}
        )
        print(f"✅ Upload SUCCESS!")
        print(f"Response: {response}")
        
        url = client.storage.from_(bucket_name).get_public_url(f"test_{bucket_name}.csv")
        print(f"Public URL: {url}")
        print(f"\n🎉 WORKING BUCKET NAME: {bucket_name}")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Upload FAILED: {e}")

print("\n❌ None of the bucket names worked!")
