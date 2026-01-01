import os
from dotenv import load_dotenv

# Test which API key is loaded
print("=== API Key Test ===\n")

# Before load_dotenv
print(f"System env GOOGLE_API_KEY: {os.environ.get('GOOGLE_API_KEY', 'NOT SET')[:20]}...")

# Load .env with override
load_dotenv(override=True)

# After load_dotenv with override
print(f"After load_dotenv(override=True): {os.getenv('GOOGLE_API_KEY', 'NOT SET')[:20]}...")

# Check .env file content
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('GOOGLE_API_KEY'):
            print(f".env file content: {line.strip()[:40]}...")
            break

print("\n=== Expected key from .env: AIzaSyATuaqXk4HAUfo...")
