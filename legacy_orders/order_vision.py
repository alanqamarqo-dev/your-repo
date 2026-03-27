import requests
import json

url = "http://127.0.0.1:8000/chat"

# نطلب منه استخدام pyautogui لالتقاط الشاشة
prompt = (
    "STRICT: Write a Python module named 'screen_eye'. "
    "Use 'pyautogui' library to take a screenshot. "
    "Save the image as 'current_view.png' in the current directory. "
    "Add a timestamp to the image filename if possible, or just overwrite. "
    "Print 'I can see your screen now.' upon success."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Vision Module...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
