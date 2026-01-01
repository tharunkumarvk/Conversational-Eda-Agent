from supabase import create_client

# Use service role key
client = create_client(
    'https://lhwptjxktbhublymzdbp.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxod3B0anhrdGJodWJseW16ZGJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIzODIwNiwiZXhwIjoyMDgyODE0MjA2fQ.i3ws4xnqE_qjFhragWWZHXK9oRrHNPeEuRLr3Ci187s'
)

print("=" * 60)
print("LISTING ALL BUCKETS WITH SERVICE ROLE")
print("=" * 60)

buckets = client.storage.list_buckets()
print(f"\nTotal buckets found: {len(buckets)}")

if buckets:
    for i, b in enumerate(buckets, 1):
        print(f"\n{i}. Bucket Details:")
        print(f"   Name: [{b.name}]")
        print(f"   ID: {b.id}")
        print(f"   Public: {b.public}")
        print(f"   Created: {b.created_at}")
else:
    print("\n⚠️  NO BUCKETS FOUND!")
    print("The bucket might not have been created properly.")

print("\n" + "=" * 60)
print("TESTING UPLOADS TO DIFFERENT NAME VARIATIONS")
print("=" * 60)

test_data = b"test,data\n1,2,3"
bucket_variations = [
    "EDA-AGENT-STORAGE",
    "eda-agent-storage", 
    "Eda-Agent-Storage",
]

for bucket_name in bucket_variations:
    print(f"\nTrying: {bucket_name}")
    try:
        response = client.storage.from_(bucket_name).upload(
            path="test_upload.csv",
            file=test_data,
            file_options={"content-type": "text/csv", "upsert": "true"}
        )
        print(f"  ✅ SUCCESS! Working bucket name: {bucket_name}")
        url = client.storage.from_(bucket_name).get_public_url("test_upload.csv")
        print(f"  Public URL: {url}")
        break
    except Exception as e:
        print(f"  ❌ Failed: {e}")
