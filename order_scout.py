import requests
import json

url = "http://127.0.0.1:8000/chat"

# الأمر: نطلب منه مقارنة الملفات الموجودة بالملفات المستوردة فعلياً
prompt = (
    "STRICT: Write a Python module named 'potential_scout'. "
    "This tool must: "
    "1. Scan 'D:\\AGL\\repo-copy' recursively to find all .py files in 'Core_Engines', 'Solvers', and 'Scientific_Systems'. "
    "2. Read the content of 'D:\\AGL\\repo-copy\\server_fixed.py'. "
    "3. Check which of the found files are NOT imported in server_fixed.py. "
    "4. Generate a report: 'Found [X] Dormant Modules'. "
    "5. List each unused module and print a suggestion: 'Recommendation: Import [Module] to enable [Functionality based on name]'. "
    "6. Save the report to 'dormant_power.txt'."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Potential Scout Tool...")
    response = requests.post(url, json=payload)

    if response.status_code == 200:
        reply = response.json().get("reply", "")
        print("\n✅ Code Generated! The scout is ready.")
        print(reply)
    else:
        print(f"❌ Error: {response.status_code}")

except Exception as e:
    print(f"Error: {e}")