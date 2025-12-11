import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'engine_loader'. "
    "This tool should dynamically import modules from 'Core_Engines' or 'Scientific_Systems'. "
    "Create a function 'load_and_run(module_name, function_name, *args)'. "
    "It must: "
    "1. Add the repo path to sys.path. "
    "2. Use importlib to load the module by name. "
    "3. Check if the function exists. "
    "4. Run it and return the result. "
    "5. Handle errors gracefully. "
    "Include a test block that tries to load 'Mathematical_Brain' (if exists) and run a dummy function."
)

payload = {"message": prompt}

try:
    print("🚀 Ordering Engine Loader...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")