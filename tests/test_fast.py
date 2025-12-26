import requests
import json

url = "http://127.0.0.1:8000/chat"
# نرسل طلب "كود" صريح لنتحدى الحارس
payload = {"message": "اكتب كود بايثون بسيط لجمع رقمين"}

try:
    print(f"🚀 Sending request to: {url}")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        reply = data.get("reply", "")
        print("\n=== Server Reply ===")
        print(reply)
        print("====================")
        
        if "Fast Engineering Core" in reply:
            print("\n✅ SUCCESS: Fast Track Activated! (⚡)")
        else:
            print("\n❌ FAIL: Request went to Quantum Core (Old Path).")
            
except Exception as e:
    print(f"Error: {e}")
