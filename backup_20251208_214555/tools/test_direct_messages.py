# Simple test to POST a `messages` payload to /chat and print response
import requests, time
url = "http://127.0.0.1:8000/chat"
payload = {
  "messages": [
    {"role": "system", "content": "أجب بالعربية: كن موجزًا وواضحًا."},
    {"role": "user", "content": "ما هي سرعة الضوء؟"}
  ]
}

for i in range(8):
    try:
        r = requests.post(url, json=payload, timeout=20)
        print('status:', r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
        break
    except Exception as e:
        print(f'Attempt {i+1} failed: {e}')
        time.sleep(1)
else:
    print('Failed to contact server after retries')
