import requests

SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxod3B0anhrdGJodWJseW16ZGJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIzODIwNiwiZXhwIjoyMDgyODE0MjA2fQ.i3ws4xnqE_qjFhragWWZHXK9oRrHNPeEuRLr3Ci187s'
BASE_URL = 'https://lhwptjxktbhublymzdbp.supabase.co'

headers = {
    'Authorization': f'Bearer {SERVICE_KEY}',
    'apikey': SERVICE_KEY
}

print("1. Listing buckets...")
response = requests.get(f'{BASE_URL}/storage/v1/bucket', headers=headers)
print(f"Status: {response.status_code}")
print(f"Buckets: {response.json()}")

print("\n2. Testing upload to EDA-AGENT-STORAGE...")
upload_headers = {
    'Authorization': f'Bearer {SERVICE_KEY}',
    'apikey': SERVICE_KEY,
    'Content-Type': 'text/csv'
}

test_data = b"test,data\n1,2,3"
upload_url = f'{BASE_URL}/storage/v1/object/EDA-AGENT-STORAGE/test_direct.csv'

response = requests.post(upload_url, headers=upload_headers, data=test_data)
print(f"Upload Status: {response.status_code}")
print(f"Upload Response: {response.text}")

if response.status_code == 200:
    print(f"\n✅ SUCCESS! Files are being stored in EDA-AGENT-STORAGE")
    public_url = f'{BASE_URL}/storage/v1/object/public/EDA-AGENT-STORAGE/test_direct.csv'
    print(f"Public URL: {public_url}")
else:
    print(f"\n❌ Upload failed")
