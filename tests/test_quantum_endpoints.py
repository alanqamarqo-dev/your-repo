import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTesting {method} {url}...")
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except:
            print("Raw Response:", response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Wait a moment for server to be fully ready if just started
    time.sleep(2)

    # 1. Test Status
    test_endpoint("GET", "/quantum/status")

    # 2. Test Volition (Quantum Tunneling)
    volition_payload = {
        "task_name": "Solve Riemann Hypothesis",
        "difficulty": 0.95,
        "importance": 0.99
    }
    test_endpoint("POST", "/quantum/volition", volition_payload)

    # 3. Test Insight (Resonance)
    insight_payload = {
        "inputs": [
            "Quantum coherence in biological systems suggests non-trivial quantum effects.",
            "Neural synchronization frequencies match predicted resonance patterns.",
            "The hard problem of consciousness requires a non-reductive explanation."
        ]
    }
    test_endpoint("POST", "/quantum/insight", insight_payload)

if __name__ == "__main__":
    main()
