import requests
import json

url = "http://127.0.0.1:8000/chat"

# نطلب منه استخدام os.walk لفهم بنيته
prompt = (
    "STRICT: Write a Python module named 'system_scanner'. "
    "Use 'os' library to scan the current directory and subdirectories. "
    "The function 'scan_structure()' should return a dictionary summarizing the project structure: "
    "{'Core_Engines': [list of files], 'dynamic_modules': [list of files], 'scripts': [list of files]}. "
    "Ignore __pycache__ and .git folders. "
    "Include a main block to print the structure nicely."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Self-Scanner Tool...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
