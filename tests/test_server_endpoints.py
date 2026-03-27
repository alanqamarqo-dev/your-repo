
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    print("🧪 Testing Server Endpoints...")
    
    # 1. Test Root Endpoint
    try:
        print("\n   1. Testing Root Endpoint (GET /)...")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("      ✅ Success!")
            print(f"      📝 Response: {response.json()}")
        else:
            print(f"      ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"      ❌ Connection Error: {e}")

    # 2. Test Chat Endpoint
    try:
        print("\n   2. Testing Chat Endpoint (POST /chat)...")
        payload = {"message": "Hello, are you online?"}
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            print("      ✅ Success!")
            print(f"      📝 Response: {response.json()}")
        else:
            print(f"      ❌ Failed: {response.status_code}")
            print(f"      📝 Error: {response.text}")
    except Exception as e:
        print(f"      ❌ Connection Error: {e}")

    # 3. Test Generate Endpoint (if available)
    try:
        print("\n   3. Testing Generate Endpoint (POST /api/generate)...")
        payload = {"prompt": "What is 2+2?"}
        response = requests.post(f"{BASE_URL}/api/generate", json=payload)
        if response.status_code == 200:
            print("      ✅ Success!")
            print(f"      📝 Response: {response.json()}")
        else:
            print(f"      ⚠️ Note: Endpoint might not be active or different path.")
            print(f"      Status: {response.status_code}")
    except Exception as e:
        print(f"      ❌ Connection Error: {e}")

if __name__ == "__main__":
    test_endpoints()
