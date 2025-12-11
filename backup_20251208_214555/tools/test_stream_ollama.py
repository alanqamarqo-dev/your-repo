import requests

url = 'http://localhost:11434/api/generate'
payload = {"model":"qwen2.5:7b-instruct","prompt":"Hello world","stream":True}
print('POST', url, 'payload=', payload)
try:
    with requests.post(url, json=payload, stream=True, timeout=20) as r:
        print('status', r.status_code)
        try:
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    print('LINE:', line)
        except Exception as e:
            print('iter_lines error:', e)
except Exception as e:
    print('request failed:', e)
