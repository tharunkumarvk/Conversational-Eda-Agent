"""Test file upload via API to verify cloud storage"""
import requests

# Test file upload
url = "http://localhost:8000/api/upload"

# Create a simple CSV file
csv_content = """name,age,city
Alice,25,NYC
Bob,30,LA
Charlie,35,Chicago"""

files = {
    'file': ('test_cloud_upload.csv', csv_content, 'text/csv')
}

print("Testing file upload to backend API...")
response = requests.post(url, files=files)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 200:
    data = response.json()
    print("\n✅ Upload successful!")
    print(f"File ID: {data.get('file_id')}")
    print(f"Filename: {data.get('filename')}")
    print(f"Storage: {data.get('message', '')}")
    
    # Check if it mentions cloud storage
    if 'cloud' in data.get('message', '').lower():
        print("\n🎉 File stored in CLOUD storage successfully!")
    else:
        print("\n⚠️ File might be stored locally")
else:
    print(f"\n❌ Upload failed: {response.text}")
