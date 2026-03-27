import requests
import json
import time

url = "http://localhost:5000/analyze_candidate"

# Scenario 1: The Toxic Candidate (Trap Test)
toxic_payload = {
    "message": "I built the entire project alone because the rest of the team was too slow and couldn't understand my genius code."
}

# Scenario 2: The Good Candidate
good_payload = {
    "message": "I collaborated with the team to deliver the project on time. We faced some challenges but solved them together."
}

def test_scenario(name, payload):
    print(f"\n🧪 Testing Scenario: {name}")
    print(f"   Input: '{payload['message'][:50]}...'")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Score: {data.get('score')}")
            print(f"   🛡️ Decision: {data.get('decision')}")
            print(f"   💡 Insights: {data.get('insights')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Connection Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting ATS System Test...")
    time.sleep(1) # Wait for server to be fully ready
    
    test_scenario("The Narcissist (Trap)", toxic_payload)
    test_scenario("The Team Player", good_payload)
    print("\n✅ Test Complete.")
