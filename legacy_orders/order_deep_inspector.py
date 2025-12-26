import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'engine_deep_inspector'. "
    "Use 'ast' library to parse 'D:\\AGL\\repo-copy\\Core_Engines\\Mathematical_Brain.py'. "
    "Iterate through all classes. For each class, list all its methods (functions inside it). "
    "Format output as: 'ClassName.MethodName'. "
    "Ignore methods starting with '_' (like __init__)."
)

payload = {"message": prompt}

try:
    print("🚀 Ordering Deep Inspector...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")