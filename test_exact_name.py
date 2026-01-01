import requests

SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxod3B0anhrdGJodWJseW16ZGJwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzIzODIwNiwiZXhwIjoyMDgyODE0MjA2fQ.i3ws4xnqE_qjFhragWWZHXK9oRrHNPeEuRLr3Ci187s'
BASE_URL = 'https://lhwptjxktbhublymzdbp.supabase.co'

upload_headers = {
    'Authorization': f'Bearer {SERVICE_KEY}',
    'apikey': SERVICE_KEY,
    'Content-Type': 'text/csv'
}

test_data = b"test,data\n1,2,3"
upload_url = f'{BASE_URL}/storage/v1/object/EDA-Agent-Storage/test_final.csv'

print("Testing upload to EDA-Agent-Storage (exact case from API)...")
response = requests.post(upload_url, headers=upload_headers, data=test_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print(f"\n✅ SUCCESS! Bucket name is: EDA-Agent-Storage")
