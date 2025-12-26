import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'native_voice'. "
    "Do NOT use 'pyttsx3' or any external library because pip is offline. "
    "Instead, use the standard 'os' library to run a PowerShell command for Text-to-Speech. "
    "The PowerShell command is: Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('TEXT'). "
    "Create a function 'speak(text)'. "
    "Include a test block."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Offline Voice Engine...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated! Check terminal output below.")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
