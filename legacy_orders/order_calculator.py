import requests
import json

# الرابط
url = "http://127.0.0.1:8000/chat"

# الأمر الصارم (لاحظ كيف حددنا الاسم والمكتبة)
prompt = (
    "STRICT: Write a Python module named 'calculator_gui'. "
    "Use 'tkinter' library to create a simple GUI calculator. "
    "It must have buttons for 0-9, +, -, *, / and =. "
    "Ensure the code includes: if __name__ == '__main__': block to run it."
)

payload = {"message": prompt}

try:
    print(f"🚀 Sending order to Genesis Core...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("\n✅ Server Response:")
        print(response.json().get("reply", ""))
        print("\n🎉 Check your 'dynamic_modules' folder now!")
    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")
