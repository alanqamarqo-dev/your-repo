import requests
import json
import time
import sys

url = "http://127.0.0.1:8000/chat"
payload = {
    "message": "مهمة: تحليل البنية التحتية للذكاء الاصطناعي في الشرق الأوسط واقتراح استراتيجية تطوير وطنية.",
    "history": []
}

print("Waiting for server...")
for i in range(30):
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=2)
        print("Server is up!")
        break
    except:
        time.sleep(2)
else:
    print("Server failed to start.")
    sys.exit(1)

print(f"Sending payload to {url}...")
try:
    start = time.time()
    response = requests.post(url, json=payload, timeout=300)
    duration = time.time() - start
    print(f"Response received in {duration:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Check for key indicators of 7B model (length, depth)
        reply = data.get("reply", "")
        print(f"\nReply Length: {len(reply)} chars")
    else:
        print(f"Error: {response.status_code} - {response.text}")

except Exception as e:
    print(f"Request failed: {e}")
