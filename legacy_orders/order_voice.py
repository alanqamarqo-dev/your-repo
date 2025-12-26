import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'voice_engine'. "
    "Use 'pyttsx3' library to create a text-to-speech function 'speak(text)'. "
    "The function must initialize the engine, set the rate to 150, say the text, and runAndWait. "
    "Include a test block that says: 'Hello, I am AGL Genesis Beta. I can speak now.'"
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Voice Engine...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated! Check terminal for output.")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
