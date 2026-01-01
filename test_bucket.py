from supabase import create_client

client = create_client(
    'https://lhwptjxktbhublymzdbp.supabase.co',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxod3B0anhrdGJodWJseW16ZGJwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjcyMzgyMDYsImV4cCI6MjA4MjgxNDIwNn0.nzyyASBWdxCSQ0vc0AseahQmLaBvWCdJ5WIWWVp30Wk'
)

print("Listing buckets...")
buckets = client.storage.list_buckets()
print(f"Buckets response: {buckets}")
print(f"Type: {type(buckets)}")

if buckets:
    for b in buckets:
        print(f"  - Name: {b.name}, ID: {b.id}, Public: {b.public}")
else:
    print("No buckets found or empty response")

# Test upload to specific bucket
print("\nTesting upload to EDA-AGENT-STORAGE...")
try:
    test_data = b"test,data\n1,2"
    response = client.storage.from_("EDA-AGENT-STORAGE").upload(
        path="test_file.csv",
        file=test_data,
        file_options={"content-type": "text/csv"}
    )
    print(f"Upload response: {response}")
    
    # Get public URL
    url = client.storage.from_("EDA-AGENT-STORAGE").get_public_url("test_file.csv")
    print(f"Public URL: {url}")
except Exception as e:
    print(f"Upload error: {e}")
