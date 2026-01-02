import sys
import os
import json
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Self_Improvement.emergency_retrieval import EmergencyRetrieval
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine

print("🕵️ Checking Emerging Capability (External Search)...")

try:
    cie = CognitiveIntegrationEngine()
    # Mock connection to avoid full system boot
    cie.adapters = [] 
    
    er = EmergencyRetrieval(cie)
    
    query = "latest developments in AGI 2025 search"
    print(f"   Querying: '{query}'")
    
    # This should trigger the external search path
    result = er.retrieve(query)
    
    print(f"   Merged Result Length: {len(result.get('merged', ''))}")
    print(f"   External Hits: {len(result.get('external_results', []))}")
    
    if result.get('external_results'):
        print("   ✅ External Search Succeeded!")
        for r in result['external_results']:
            print(f"      - {r['title']} ({r['url']})")
    else:
        print("   ⚠️ External Search Failed (Network Blocked?). Checking Airgap Request...")
        
        req_file = os.path.join("artifacts", "airgap_search_requests.json")
        if os.path.exists(req_file):
            with open(req_file, 'r', encoding='utf-8') as f:
                reqs = json.load(f)
            
            found = any(r['query'] == query for r in reqs)
            if found:
                print("   ✅ Airgap Request Successfully Queued!")
            else:
                print("   ❌ Airgap Request NOT found.")
        else:
            print("   ❌ Airgap Request File NOT found.")

except Exception as e:
    print(f"   ❌ Error: {e}")
