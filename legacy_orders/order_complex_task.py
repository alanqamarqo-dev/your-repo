import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Execute a multi-step engineering task.\n"
    "1. Write a Python module 'stats_cruncher.py'.\n"
    "2. Inside, generate a list of 100 random integers (1-1000).\n"
    "3. Implement a function to calculate Mean and Standard Deviation manually (without numpy).\n"
    "4. In the main block, run the calculation and PRINT the results clearly.\n"
    "5. Save the file and ensure it is runnable.\n"
)

payload = {"message": prompt}

try:
    print("🚀 Challenging AGL Engines...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Challenge Accepted:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")