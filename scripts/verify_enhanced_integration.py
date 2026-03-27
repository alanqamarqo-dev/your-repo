import requests
import time
import sys
import json

def verify_integration():
    url = "http://127.0.0.1:8000/chat"
    
    # Wait for server to start (assuming it's launched just before this script)
    print("⏳ Waiting for server to be ready...")
    time.sleep(5) 
    
    # 1. Test Strategic/Enhanced Path
    # Using a keyword that triggers the router: "صمم" (Design)
    payload = {
        "message": "صمم نظام تبريد لمفاعل نووي على المريخ"
    }
    
    print(f"\n📤 Sending Strategic Request: {payload['message']}")
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response Received (Took {duration:.2f}s)")
            
            reply = data.get('reply', '')
            meta = data.get('meta', {})
            
            print("\n--- 🔍 Verification Report ---")
            
            # Check 1: Engine Routing
            engine = meta.get('engine')
            if engine in ['Enhanced_Mission_Control', 'EnhancedMissionController']:
                print(f"✅ Routing: Correct ({engine})")
            else:
                print(f"❌ Routing: Failed (Got '{engine}', expected 'Enhanced_Mission_Control')")
            
            # Check 2: Output Cleanliness (Modified Expectation: Data SHOULD be present now)
            if "System Simulation Data" in reply or "Mathematical Proof" in reply:
                print("✅ Output Format: Verified (Scientific data IS present in reply as requested)")
            else:
                print("❌ Output Format: Failed (Scientific data missing from reply)")
                
            # Check 3: Metadata Presence
            if 'simulation_data' in meta or 'proof_data' in meta:
                print("✅ Metadata: Scientific data correctly moved to meta")
                if meta.get('simulation_data'):
                    sim_data = str(meta['simulation_data'])
                    print(f"   - Simulation Data: Present ({len(sim_data)} chars)")
                    print(f"   - Snippet: {sim_data[:200]}...")
                else:
                    print("   - Simulation Data: None (Expected for some queries)")
            else:
                print("⚠️ Metadata: Scientific keys missing from meta")

            print("-" * 50)
            print(f"🤖 Final Reply Snippet: {reply[:100]}...")
            print("-" * 50)
            
        else:
            print(f"❌ Error: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_integration()
