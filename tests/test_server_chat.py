
import requests
import time
import sys

def test_chat_endpoint():
    url = "http://127.0.0.1:8000/chat"
    
    # Wait for server to start
    print("⏳ Waiting for server to be ready...")
    time.sleep(10) 
    
    payload = {
        "message": "Explain the concept of time dilation in simple terms."
    }
    
    print(f"📤 Sending request: {payload['message']}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! (Took {duration:.2f}s)")
            print("-" * 50)
            print(f"🤖 Reply: {data.get('reply')}")
            print("-" * 50)
            print(f"🧠 Meta: {data.get('meta')}")
        else:
            print(f"❌ Error: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    test_chat_endpoint()
