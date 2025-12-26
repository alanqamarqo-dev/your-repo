import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'engine_inspector'. "
    "Use 'ast' library to parse 'D:\\AGL\\repo-copy\\Core_Engines\\Mathematical_Brain.py'. "
    "Find all function definitions (def ...) and class definitions. "
    "Print their names. "
    "Handle FileNotFoundError gracefully."
)

payload = {"message": prompt}

try:
    print("🚀 Inspecting Mathematical Brain...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Inspector Code:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")