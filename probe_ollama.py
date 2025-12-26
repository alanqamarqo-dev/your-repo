import requests
import os

def probe():
    base = os.environ.get('AGL_LLM_BASEURL', 'http://localhost:11434')
    print(f"Probing {base}...")
    
    paths = [
        '/',
        '/api/tags',
        '/api/generate',
        '/v1/models',
        '/v1/chat/completions'
    ]
    
    # Try POST to /api/generate
    url = base.rstrip('/') + '/api/generate'
    print(f"\nTesting POST to {url}...")
    payload = {
        "model": "qwen2.5:7b-instruct",
        "prompt": "Hi",
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"POST Status: {resp.status_code}")
        if resp.status_code != 200:
            print(resp.text)
        else:
            print("Success!")
    except Exception as e:
        print(f"POST Error: {e}")

if __name__ == "__main__":
    probe()