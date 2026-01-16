import json
import os
import time

REQUEST_FILE = "d:\\AGL\\artifacts\\airgap_search_requests.json"
RESPONSE_FILE = "d:\\AGL\\artifacts\\airgap_search_responses.json"

def request_search(query):
    """
    Writes a search request to the airgap file.
    """
    print(f"📡 [AirGap Bridge] Requesting search for: '{query}'")
    
    requests = []
    if os.path.exists(REQUEST_FILE):
        try:
            with open(REQUEST_FILE, 'r', encoding='utf-8') as f:
                requests = json.load(f)
        except:
            pass
            
    requests.append({
        "id": int(time.time()),
        "query": query,
        "status": "pending",
        "timestamp": time.ctime()
    })
    
    with open(REQUEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(requests, f, indent=2, ensure_ascii=False)
        
    print(f"   ✅ Request written to {REQUEST_FILE}")
    print("   👉 ACTION REQUIRED: Transfer this file to a connected machine, run the search, and place results in 'airgap_search_responses.json'.")

def check_responses():
    """
    Checks for responses from the outside world.
    """
    if not os.path.exists(RESPONSE_FILE):
        print("   📭 No responses found yet.")
        return []
        
    try:
        with open(RESPONSE_FILE, 'r', encoding='utf-8') as f:
            responses = json.load(f)
        
        print(f"   📬 Found {len(responses)} responses!")
        return responses
    except Exception as e:
        print(f"   ❌ Error reading responses: {e}")
        return []

if __name__ == "__main__":
    # Example usage
    request_search("Latest advancements in AGI 2025")
    check_responses()
