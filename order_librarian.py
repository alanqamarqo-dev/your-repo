import requests
import json

url = "http://127.0.0.1:8000/chat"

prompt = (
    "STRICT: Write a Python module named 'local_librarian'. "
    "Create a function 'read_text_file(filepath)'. "
    "1. It must accept a file path. "
    "2. Check if file exists using os.path. "
    "3. Open and read the file (utf-8). "
    "4. Return the content string. "
    "5. Handle errors (FileNotFound, PermissionError). "
    "Include a main block that tries to read 'D:\\AGL\\README.txt' (create this file manually to test)."
)

payload = {"message": prompt}

try:
    print(f"🚀 Ordering Librarian Tool...")
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("\n✅ Code Generated:\n")
        print(response.json().get("reply", ""))
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
